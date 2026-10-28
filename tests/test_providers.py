"""Sin red: pruebas de respaldo y presupuesto usando clientes simulados."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
from src.priv_audit.providers import ProviderRouter, FallbackBudget, FallbackBudgetError


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
        router=ProviderRouter(primary,backup,FallbackBudget())
        self.assertEqual(router.create(**self.kwargs),'ok')
        backup.chat.completions.create.assert_not_called()

    def test_timeout_quota_and_outage_switch_once_and_keep_state(self):
        for error in [TimeoutError(),Failure(408),Failure(429),Failure(503)]:
            with self.subTest(error=type(error).__name__):
                primary, backup = client(side_effect=error), client(return_value='backup')
                callback=Mock()
                router=ProviderRouter(primary,backup,FallbackBudget(),on_switch=callback)
                self.assertEqual(router.create(**self.kwargs),'backup')
                self.assertEqual(router.create(**self.kwargs),'backup')
                self.assertEqual(primary.chat.completions.create.call_count,1)
                self.assertEqual(backup.chat.completions.create.call_count,2)
                callback.assert_called_once()
                params=backup.chat.completions.create.call_args.kwargs
                self.assertEqual(params['max_tokens'],1536)
                self.assertNotIn('max_completion_tokens',params)
                self.assertEqual(params['reasoning_effort'],'minimal')
                self.assertEqual(params['messages'],self.kwargs['messages'])

    def test_invalid_request_credentials_or_context_does_not_spend_backup(self):
        for status in [400,401,403,413]:
            primary, backup = client(side_effect=Failure(status)), client()
            with self.assertRaises(Failure):
                ProviderRouter(primary,backup,FallbackBudget()).create(**self.kwargs)
            backup.chat.completions.create.assert_not_called()

    def test_without_key_original_error_is_preserved(self):
        primary, backup=client(side_effect=Failure(503)),client()
        with patch.dict('os.environ',{'GEMINI_API_KEY':''}),self.assertRaises(Failure):
            ProviderRouter(primary,backup,FallbackBudget()).create(**self.kwargs)
        backup.chat.completions.create.assert_not_called()

    def test_google_errors_are_not_retried(self):
        primary, backup=client(side_effect=Failure(503)),client(side_effect=Failure(429))
        router=ProviderRouter(primary,backup,FallbackBudget())
        with self.assertRaises(Failure):
            router.create(**self.kwargs)
        self.assertEqual(backup.chat.completions.create.call_count,1)
        self.assertEqual(router.calls,1)

    def test_oversized_context_is_refused_before_request(self):
        primary, backup=client(side_effect=Failure(503)),client()
        router=ProviderRouter(primary,backup,FallbackBudget())
        self.kwargs['messages'][0]['content']='x'*24001
        with self.assertRaises(FallbackBudgetError):
            router.create(**self.kwargs)
        backup.chat.completions.create.assert_not_called()

    def test_budget_is_shared_between_independent_tasks(self):
        budget=FallbackBudget(calls=1)
        for index in range(2):
            primary, backup=client(side_effect=Failure(503)),client(return_value='ok')
            router=ProviderRouter(primary,backup,budget)
            if index==0:
                router.create(**self.kwargs)
            else:
                with self.assertRaises(FallbackBudgetError):
                    router.create(**self.kwargs)
                backup.chat.completions.create.assert_not_called()

    def test_task_budget_stops_repeated_requests(self):
        primary,backup=client(side_effect=Failure(503)),client(return_value='ok')
        router=ProviderRouter(primary,backup,FallbackBudget())
        self.kwargs['max_completion_tokens']=100
        for _ in range(6):
            router.create(**self.kwargs)
        with self.assertRaises(FallbackBudgetError):
            router.create(**self.kwargs)
        self.assertEqual(backup.chat.completions.create.call_count,6)

    def test_output_reservations_are_enforced_before_request(self):
        primary,backup=client(side_effect=Failure(503)),client(return_value='ok')
        router=ProviderRouter(primary,backup,FallbackBudget())
        for _ in range(3):
            router.create(**self.kwargs)
        with self.assertRaises(FallbackBudgetError):
            router.create(**self.kwargs)
        self.assertEqual(backup.chat.completions.create.call_count,3)

    def test_empty_groq_answer_activates_fallback(self):
        empty=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None,tool_calls=[]))])
        primary, backup=client(return_value=empty),client(return_value='backup')
        self.assertEqual(ProviderRouter(primary,backup,FallbackBudget()).create(**self.kwargs),'backup')

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
            router=ProviderRouter(client(side_effect=Failure(503)),backup,FallbackBudget())
            result=router.create(**self.kwargs)
            body=json.loads(requests[0].content)
            self.assertEqual(requests[0].url.path,'/v1beta/openai/chat/completions')
            self.assertEqual(body['max_tokens'],1536)
            call=result.choices[0].message.tool_calls[0].model_dump()
            self.assertEqual(call['extra_content']['google']['thought_signature'],'opaque-test-value')

    @patch('src.priv_audit.rag_loader.diagnostico_documentos', return_value=[])
    def test_agent_completes_using_backup_and_reports_provider(self, _):
        from src.priv_audit.agent import PrivacyAgent
        from tests.test_agent import response, call, REASON
        backup=client(side_effect=[
            response(call('cargar_skill',dict(REASON,nombre='consulta_pims'))),
            response(call('finalizar_consulta',dict(REASON,estado='fuera_de_alcance',conclusiones=[],limitaciones=['Tema ajeno al dominio.'])))])
        router=ProviderRouter(client(side_effect=Failure(503)),backup,FallbackBudget())
        result=PrivacyAgent(task='consulta',objective='Receta de cocina',client=router).run()
        self.assertEqual(result['respaldo']['proveedor_actual'],'gemini')
        self.assertEqual(result['respaldo']['llamadas_gemini'],2)
        self.assertEqual(result['modelo'],'gemini-3.5-flash-lite')
        self.assertEqual(result['estado_respuesta'],'fuera_de_alcance')
