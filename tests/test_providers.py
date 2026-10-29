"""Sin red: pruebas de respaldo sin cuotas locales usando clientes simulados."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
from src.priv_audit.providers import ProviderRouter


class Failure(Exception):
    def __init__(self, status):
        self.status_code = status


def client(**options):
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=Mock(**options))))


class FallbackTests(TestCase):
    def setUp(self):
        self.environment = patch.dict('os.environ', {'GEMINI_API_KEY':'test-only-not-real', 'GEMINI_MODEL':'gemini-3.5-flash-lite'})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.kwargs = dict(model='openai/gpt-oss-120b', messages=[{'role':'user','content':'Consulta breve'}],
                           max_completion_tokens=3000, reasoning_effort='low')

    def test_healthy_groq_never_calls_google(self):
        primary, backup = client(return_value='ok'), client(return_value='backup')
        router=ProviderRouter(primary,backup)
        self.assertEqual(router.create(**self.kwargs),'ok')
        backup.chat.completions.create.assert_not_called()

    def test_timeout_quota_and_outage_switch_once_and_keep_state(self):
        for error in [TimeoutError(),Failure(408),Failure(429),Failure(503)]:
            with self.subTest(error=type(error).__name__):
                primary, backup = client(side_effect=error), client(return_value='backup')
                callback=Mock()
                router=ProviderRouter(primary,backup,on_switch=callback)
                self.assertEqual(router.create(**self.kwargs),'backup')
                self.assertEqual(router.create(**self.kwargs),'backup')
                self.assertEqual(primary.chat.completions.create.call_count,1)
                self.assertEqual(backup.chat.completions.create.call_count,2)
                callback.assert_called_once()
                params=backup.chat.completions.create.call_args.kwargs
                self.assertEqual(params['max_tokens'],3000)
                self.assertNotIn('max_completion_tokens',params)
                self.assertEqual(params['reasoning_effort'],'minimal')
                self.assertEqual(params['messages'],self.kwargs['messages'])

    def test_invalid_request_credentials_or_context_does_not_spend_backup(self):
        for status in [400,401,403,413]:
            primary, backup = client(side_effect=Failure(status)), client()
            with self.assertRaises(Failure):
                ProviderRouter(primary,backup).create(**self.kwargs)
            backup.chat.completions.create.assert_not_called()

    def test_without_key_original_error_is_preserved(self):
        primary, backup=client(side_effect=Failure(503)),client()
        with patch.dict('os.environ',{'GEMINI_API_KEY':''}),self.assertRaises(Failure):
            ProviderRouter(primary,backup).create(**self.kwargs)
        backup.chat.completions.create.assert_not_called()

    def test_google_errors_are_not_retried(self):
        primary, backup=client(side_effect=Failure(503)),client(side_effect=Failure(429))
        router=ProviderRouter(primary,backup)
        with self.assertRaises(Failure):
            router.create(**self.kwargs)
        self.assertEqual(backup.chat.completions.create.call_count,1)
        self.assertEqual(router.calls,1)

    def test_large_context_and_repeated_calls_have_no_local_quota(self):
        primary, backup = client(side_effect=Failure(503)), client(return_value='ok')
        router = ProviderRouter(primary, backup)
        self.kwargs['messages'][0]['content'] = 'x' * 100000
        self.kwargs['max_completion_tokens'] = 8000
        for _ in range(20):
            self.assertEqual(router.create(**self.kwargs), 'ok')
        self.assertEqual(backup.chat.completions.create.call_count, 20)
        params = backup.chat.completions.create.call_args.kwargs
        self.assertEqual(params['messages'], self.kwargs['messages'])
        self.assertEqual(params['max_tokens'], 8000)
        self.assertEqual(router.summary()['llamadas_gemini'], 20)
        other = ProviderRouter(client(side_effect=Failure(503)), backup)
        self.assertEqual(other.create(**self.kwargs), 'ok')

    def test_switch_transports_groq_tools_as_text_and_keeps_google_signatures(self):
        from copy import deepcopy
        old_call = {'id':'groq-1','type':'function','function':{'name':'cargar_skill','arguments':'{}'}}
        signed_call = dict(old_call, id='google-1', extra_content={'google':{'thought_signature':'opaque'}})
        messages = [
            {'role':'user','content':'Audita SQL'},
            {'role':'assistant','content':None,'tool_calls':[old_call]},
            {'role':'tool','tool_call_id':'groq-1','content':'Skill cargada: auditoria_sql'}]
        original = deepcopy(messages)
        primary, backup = client(side_effect=Failure(429)), client(return_value='ok')
        router = ProviderRouter(primary, backup)
        router.create(**dict(self.kwargs, messages=messages))
        sent = backup.chat.completions.create.call_args.kwargs['messages']
        self.assertNotIn('tool_calls', sent[1])
        self.assertIn('cargar_skill', sent[1]['content'])
        self.assertEqual(sent[2]['role'], 'user')
        self.assertIn('Skill cargada', sent[2]['content'])
        self.assertEqual(messages, original)
        messages += [{'role':'assistant','content':None,'tool_calls':[signed_call]},
                     {'role':'tool','tool_call_id':'google-1','content':'Resultado Google'}]
        router.create(**dict(self.kwargs, messages=messages))
        sent = backup.chat.completions.create.call_args.kwargs['messages']
        self.assertEqual(sent[-2:], messages[-2:])
        # Compactar la conversación no cambia la identificación de llamadas Groq.
        router.create(**dict(self.kwargs, messages=messages[1:]))
        sent = backup.chat.completions.create.call_args.kwargs['messages']
        self.assertNotIn('tool_calls', sent[0])
        self.assertEqual(sent[-2:], messages[-2:])

    def test_empty_groq_answer_activates_fallback(self):
        empty=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None,tool_calls=[]))])
        primary, backup=client(return_value=empty),client(return_value='backup')
        self.assertEqual(ProviderRouter(primary,backup).create(**self.kwargs),'backup')

    def test_gemini_rest_request_and_tool_metadata_roundtrip_without_network(self):
        import httpx
        import json
        from openai import OpenAI
        requests=[]
        def handler(request):
            requests.append(request)
            return httpx.Response(200,json={
                'id':'mock-completion','object':'chat.completion','created':0,'model':'gemini-3.5-flash-lite',
                'choices':[{'index':0,'finish_reason':'tool_calls','message':{
                    'role':'assistant','content':None,'tool_calls':[{
                        'id':'tool1','type':'function','function':{'name':'cargar_skill','arguments':'{"nombre":"consulta_pims","motivo":"Consultar fuentes."}'},
                        'extra_content':{'google':{'thought_signature':'opaque-test-value'}}}]}}],
                'usage':{'prompt_tokens':12,'completion_tokens':8,'total_tokens':20}})
        with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
            backup=OpenAI(api_key='fake-only',base_url='https://generativelanguage.googleapis.com/v1beta/openai/',http_client=transport,max_retries=0)
            router=ProviderRouter(client(side_effect=Failure(503)),backup)
            result=router.create(**self.kwargs)
            body=json.loads(requests[0].content)
            self.assertEqual(requests[0].url.path,'/v1beta/openai/chat/completions')
            self.assertEqual(body['max_tokens'],3000)
            call=result.choices[0].message.tool_calls[0].model_dump()
            self.assertEqual(call['extra_content']['google']['thought_signature'],'opaque-test-value')

    @patch('src.priv_audit.rag_loader.diagnostico_documentos', return_value=[])
    def test_agent_completes_using_backup_and_reports_provider(self, _):
        from src.priv_audit.agent import PrivacyAgent
        from tests.test_agent import response, call, REASON
        backup=client(side_effect=[
            response(call('cargar_skill',dict(REASON,nombre='consulta_pims'))),
            response(call('finalizar_consulta',dict(REASON,estado='fuera_de_alcance',conclusiones=[],limitaciones=['Tema ajeno al dominio.'])))])
        router=ProviderRouter(client(side_effect=Failure(503)),backup)
        result=PrivacyAgent(task='consulta',objective='Receta de cocina',client=router).run()
        self.assertEqual(result['respaldo']['proveedor_actual'],'gemini')
        self.assertEqual(result['respaldo']['llamadas_gemini'],2)
        self.assertEqual(result['modelo'],'gemini-3.5-flash-lite')
        self.assertEqual(result['estado_respuesta'],'fuera_de_alcance')
