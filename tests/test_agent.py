"""Pruebas del ciclo y sus fronteras. No realizan llamadas remotas."""
import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from src.priv_audit.agent import PrivacyAgent, AgentError, tools_for
from src.priv_audit.jobs import RunStore
from web_app import app

SQL = 'CREATE TABLE persona (dni VARCHAR(8), religion TEXT);'
REASON = {'motivo': 'Comprobar evidencia antes de concluir.'}
CHUNK = dict(id='evidence123', texto='Artículo 9. Principio de seguridad de datos personales.',
             fuente='ley.pdf', pagina=2, url='https://example.org/ley.pdf', tipo_fuente='primaria')


def draft(**changes):
    finding = dict(tabla='persona', campos_afectados=['dni'], descripcion_hallazgo='Identificación personal que requiere revisión.',
                   evidencia='dni VARCHAR(8)', nivel_riesgo='MEDIO', riesgo_potencial='Exposición potencial.',
                   informacion_faltante='Finalidad y acceso efectivo.', recomendacion_mitigacion='Revisar acceso por rol.',
                   criterio_normativo='No confiar en este texto inventado.')
    finding.update(changes)
    return dict(REASON, hallazgos=[finding], resumen_ejecutivo='Un indicio para revisión.', tablas_revisadas=['persona'])


def ready_agent():
    agent = PrivacyAgent(sql=SQL)
    agent.execute('cargar_skill', dict(REASON, nombre='auditoria_sql'))
    agent.execute('inspeccionar_esquema', REASON)
    agent.searches = 1
    agent.evidence[CHUNK['id']] = CHUNK.copy()
    return agent


def call(name, args):
    return SimpleNamespace(id='call_' + name, function=SimpleNamespace(name=name, arguments=json.dumps(args)),
                           model_dump=lambda: {'id': 'call_' + name, 'type': 'function',
                                               'function': {'name': name, 'arguments': json.dumps(args)}})


def response(tool):
    return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=20, completion_tokens=10),
                           choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tool]))])


class AgentValidationTests(TestCase):
    def test_skill_and_inspection_are_enforced(self):
        agent = PrivacyAgent(sql=SQL)
        with self.assertRaisesRegex(ValueError, 'skill'):
            agent.execute('inspeccionar_esquema', REASON)
        agent.execute('cargar_skill', dict(REASON, nombre='auditoria_sql'))
        with self.assertRaisesRegex(ValueError, 'inspecciona'):
            agent.execute('aplicar_reglas_locales', REASON)

    def test_rejects_fake_columns_and_nonliteral_sql(self):
        for changes in ({'campos_afectados': ['inventado']}, {'evidencia': 'dni TEXT'}, {'campos_afectados': []}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                ready_agent().execute('validar_informe', draft(**changes))

    def test_rejects_unretrieved_or_fabricated_citation(self):
        for ref in ({'fragmento_id':'unknown', 'cita':'Principio de seguridad'},
                    {'fragmento_id':CHUNK['id'], 'cita':'Texto completamente inventado'}):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                ready_agent().execute('validar_informe', draft(referencias=[ref]))

    def test_editorial_note_cannot_become_normative_evidence(self):
        agent = ready_agent()
        agent.evidence[CHUNK['id']]['tipo_fuente'] = 'ficha_publica'
        with self.assertRaisesRegex(ValueError, 'primario'):
            agent.execute('validar_informe', draft(referencias=[{'fragmento_id':CHUNK['id'], 'cita':'Principio de seguridad'}]))

    def test_verified_reference_metadata_is_server_owned(self):
        agent = ready_agent()
        output = agent.execute('validar_informe', draft(referencias=[{'fragmento_id':CHUNK['id'], 'cita':'Principio de seguridad'}]))
        agent.execute('finalizar_auditoria', dict(REASON, borrador_id=output['borrador_id']))
        h = agent.result['hallazgos'][0]
        self.assertNotIn('inventado', h['criterio_normativo'])
        self.assertEqual(h['referencias'][0]['pagina'], 2)

    def test_whitespace_is_resolved_to_original_sql_without_changing_tokens(self):
        agent = ready_agent()
        agent.sql = 'CREATE TABLE persona (dni       VARCHAR(8), religion TEXT);'
        result = agent.execute('validar_informe', draft())
        h = agent.drafts[result['borrador_id']]['hallazgos'][0]
        self.assertEqual(h['evidencia'], 'dni       VARCHAR(8)')
        self.assertIn(h['evidencia'], agent.sql)

    def test_report_without_sources_is_explicitly_pending(self):
        agent = ready_agent()
        output = agent.execute('validar_informe', draft())
        self.assertIn('pendiente', agent.drafts[output['borrador_id']]['hallazgos'][0]['criterio_normativo'])

    def test_cannot_finish_unvalidated_draft(self):
        with self.assertRaisesRegex(ValueError, 'validado'):
            ready_agent().execute('finalizar_auditoria', dict(REASON, borrador_id='inventado'))

    def test_all_tables_must_be_declared(self):
        payload = draft()
        payload['tablas_revisadas'] = []
        with self.assertRaisesRegex(ValueError, 'todas'):
            ready_agent().execute('validar_informe', payload)

    def test_first_skill_is_the_task_skill_before_optional_review(self):
        for task, expected in [('auditoria', 'auditoria_sql'), ('consulta', 'consulta_pims')]:
            agent = PrivacyAgent(task=task, sql=SQL if task == 'auditoria' else '')
            tools = agent.available_tools()
            self.assertEqual(len(tools), 1)
            self.assertEqual(tools[0]['function']['parameters']['properties']['nombre']['enum'], [expected])

    def test_consultation_tools_cannot_inspect_or_modify_database(self):
        names = {t['function']['name'] for t in tools_for('consulta')}
        self.assertEqual(names, {'cargar_skill','buscar_documentos','finalizar_consulta'})
        with self.assertRaises(ValueError):
            PrivacyAgent(task='consulta').execute('inspeccionar_esquema', REASON)
        self.assertNotIn('$ref', json.dumps(tools_for('auditoria')))

    def test_insufficient_evidence_requires_search_and_no_conclusions(self):
        agent = PrivacyAgent(task='consulta')
        agent.execute('cargar_skill', dict(REASON, nombre='consulta_pims'))
        payload = dict(REASON, estado='evidencia_insuficiente', conclusiones=[], limitaciones=['Falta evidencia.'])
        with self.assertRaisesRegex(ValueError, 'Busca'):
            agent.execute('finalizar_consulta', payload)
        agent.searches = 1
        agent.execute('finalizar_consulta', payload)
        self.assertEqual(agent.result['estado_respuesta'], 'evidencia_insuficiente')

    def test_scope_rejection_has_no_generated_answer(self):
        agent = PrivacyAgent(task='consulta')
        agent.execute('cargar_skill', dict(REASON, nombre='consulta_pims'))
        agent.execute('finalizar_consulta', dict(REASON, estado='fuera_de_alcance', conclusiones=[], limitaciones=['Tema fuera de PIMS.']))
        self.assertEqual(agent.result['conclusiones'], [])

    def test_unknown_document_filter_returns_actionable_error(self):
        agent = ready_agent()
        retriever = SimpleNamespace(chunks=[CHUNK])
        with patch('src.priv_audit.agent.obtener_retriever', return_value=retriever):
            with self.assertRaisesRegex(ValueError, 'ley.pdf'):
                agent.execute('buscar_documentos', dict(REASON, consulta='seguridad', fuente='inventado.pdf'))

    def test_compaction_preserves_current_tool_exchange_and_original_goal(self):
        agent = ready_agent()
        last = [dict(role='assistant', tool_calls=[{'id':'latest','function':{'name':'cargar_skill'}}]),
                dict(role='tool', tool_call_id='latest', content='Skill cargada')]
        messages = [dict(role='system', content='Reglas'), dict(role='user', content=SQL),
                    dict(role='assistant', tool_calls=[{'id':'old'}]),
                    dict(role='tool', tool_call_id='old', content='x' * 22000)] + last
        compact = agent.compact_messages(messages)
        self.assertEqual(compact[:2], messages[:2])
        self.assertEqual(compact[-2:], last)
        self.assertLess(len(json.dumps(compact)),len(json.dumps(messages)))
        self.assertIn('evidence123', compact[2]['content'])


class AgentLoopTests(TestCase):
    @patch('src.priv_audit.rag_loader.diagnostico_documentos', return_value=[])
    def test_model_receives_rejection_and_adapts_next_action(self, _):
        actions = [call('inspeccionar_esquema', REASON),
                   call('cargar_skill', dict(REASON, nombre='consulta_pims')),
                   call('finalizar_consulta', dict(REASON, estado='fuera_de_alcance', conclusiones=[], limitaciones=['Tema ajeno al dominio.']))]
        histories = []
        def create(**kwargs):
            histories.append(json.loads(json.dumps(kwargs['messages'])))
            return response(actions.pop(0))
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        result = PrivacyAgent(task='consulta', objective='Receta de cocina', client=client).run()
        self.assertEqual(result['turnos'], 3)
        self.assertTrue(any(e['estado'] == 'rechazado' for e in result['traza']))
        self.assertIn('error', histories[1][-1]['content'])
        self.assertEqual(result['estado_respuesta'], 'fuera_de_alcance')

    @patch('src.priv_audit.rag_loader.diagnostico_documentos', return_value=[])
    @patch('src.priv_audit.agent.MAX_TURNS', 2)
    def test_step_limit_stops_nonprogressing_model(self, _):
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **kwargs: response(call('cargar_skill', dict(REASON, nombre='consulta_pims'))))))
        with self.assertRaisesRegex(AgentError, 'límite'):
            PrivacyAgent(task='consulta', objective='Privacidad', client=client).run()

    @patch('src.priv_audit.rag_loader.diagnostico_documentos', return_value=[])
    def test_provider_tool_validation_error_is_returned_for_correction(self, _):
        class ProviderError(Exception):
            body = {'error': {'code':'tool_use_failed','message':'Unknown tool json'}}
        outputs = [ProviderError(), response(call('cargar_skill', dict(REASON, nombre='consulta_pims'))),
                   response(call('finalizar_consulta', dict(REASON, estado='fuera_de_alcance', conclusiones=[], limitaciones=['Tema ajeno.'])))]
        def create(**kwargs):
            value = outputs.pop(0)
            if isinstance(value, Exception):
                raise value
            return value
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        result = PrivacyAgent(task='consulta', objective='Receta', client=client).run()
        self.assertEqual(result['turnos'], 3)
        self.assertTrue(any(e['herramienta'] == 'llamada_herramienta' for e in result['traza']))

    @patch('src.priv_audit.rag_loader.diagnostico_documentos', return_value=[])
    @patch('src.priv_audit.agent.time.sleep')
    def test_quota_wait_does_not_consume_model_decision(self, sleep, _):
        class QuotaError(Exception):
            status_code = 429
            response = SimpleNamespace(headers={'retry-after':'1'})
        outputs = [QuotaError(), response(call('cargar_skill', dict(REASON, nombre='consulta_pims'))),
                   response(call('finalizar_consulta', dict(REASON, estado='fuera_de_alcance', conclusiones=[], limitaciones=['Tema ajeno.'])))]
        def create(**kwargs):
            value = outputs.pop(0)
            if isinstance(value, Exception):
                raise value
            return value
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        result = PrivacyAgent(task='consulta', objective='Receta', client=client).run()
        self.assertEqual(result['turnos'], 2)
        self.assertEqual(result['solicitudes'], 3)
        sleep.assert_called_once()

    @patch('src.priv_audit.rag_loader.diagnostico_documentos', return_value=[])
    def test_provider_error_body_is_not_exposed(self, _):
        def create(**kwargs):
            raise RuntimeError('secret-key-must-not-appear')
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        with self.assertRaises(AgentError) as caught:
            PrivacyAgent(task='consulta', objective='Privacidad', client=client).run()
        self.assertNotIn('secret-key', str(caught.exception))
        self.assertNotIn('secret-key', json.dumps(caught.exception.trace))


class AgentAPITests(TestCase):
    def test_missing_key_and_invalid_payload_do_not_start_work(self):
        with app.test_client() as client, patch.dict('os.environ', {'GROQ_API_KEY':''}):
            self.assertEqual(client.post('/api/agent/runs', json={'tarea':'consulta','objetivo':'Agentes'}).status_code,400)
        with app.test_client() as client, patch.dict('os.environ', {'GROQ_API_KEY':'fake'}):
            for data in ({'tarea':'consulta','objetivo':''},{'tarea':'otra'}, {'sql':'SELECT 1'}):
                self.assertEqual(client.post('/api/agent/runs', json=data).status_code,400)
            self.assertEqual(client.get('/api/agent/runs/no-existe').status_code,404)

    def test_store_bounds_concurrent_jobs(self):
        store = RunStore(workers=1)
        with patch.object(store.executor, 'submit'):
            key = store.start({'tarea':'consulta'})
            with self.assertRaises(ValueError):
                store.start({'tarea':'consulta'})
            value = store.get(key)
            value['traza'].append('no mutar estado compartido')
            self.assertEqual(store.get(key)['traza'], [])
        store.executor.shutdown(wait=False)

    def test_async_audit_publishes_trace_and_result_without_remote_call(self):
        from threading import Event
        from src.priv_audit.jobs import runs
        done = Event()
        def fake_audit(sql, mode, dialect, objective, callback):
            callback({'herramienta':'inspeccionar_esquema','estado':'completado','motivo':'Revisar entrada.',
                      'resultado':'Una tabla.', 'segundos':0.01})
            done.set()
            return {'hallazgos':[], 'modo':'ai'}
        with app.test_client() as client, patch.dict('os.environ', {'GROQ_API_KEY':'fake'}), patch(
            'src.priv_audit.jobs.audit', side_effect=fake_audit
        ):
            started = client.post('/api/agent/runs', json={'tarea':'auditoria','sql':SQL})
            self.assertEqual(started.status_code,202)
            self.assertTrue(done.wait(2))
            # The worker updates the result just after publishing the event.
            import time
            result = None
            for _ in range(100):
                result = client.get('/api/agent/runs/' + started.json['id']).json
                if result['estado'] == 'completado':
                    break
                time.sleep(.01)
            self.assertEqual(result['estado'],'completado')
            self.assertEqual(result['resultado']['modo'],'ai')
            self.assertEqual(result['traza'][0]['herramienta'],'inspeccionar_esquema')
