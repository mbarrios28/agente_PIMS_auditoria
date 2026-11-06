import copy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from src.priv_audit import history
from src.priv_audit.publication import preview,confirm,reconcile,load_preview,PublicationError,UncertainWrite
from src.priv_audit.risk import from_gestitel
from web_app import app

class FakeGateway:
    def __init__(self):
        self.asset=dict(id=1,code='ACT-1',name='Servidor',updated_at='v1',risk_eligible=True)
        self.matrix=dict(id=2,name='Matriz 4x4',dimension=4,status='A',usage='A',updated_at='v1',
            levels=[dict(axis=a,value=str(v)) for a in ('P','I') for v in range(1,5)],
            risk_ranges=[dict(level=n,min_value=a,max_value=b) for n,a,b in [('L',1,3),('M',4,7),('H',8,11),('C',12,16)]])
        self.period=dict(id=1,status='O',is_active=True)
        self.control=dict(id=72,code='A.8.13',description='Copias')
        self.records={};self.writes=[];self.uncertain=False
    def get(self,path):
        if path=='/api/assets/1/':return copy.deepcopy(self.asset)
        if path.startswith('/api/evaluation-matrices/'):return dict(results=[copy.deepcopy(self.matrix)])
        if path=='/api/risk-evaluations/catalogs/':return dict(current_period=copy.deepcopy(self.period),applicable_annex_a_controls=[dict(code='A.8.13')])
        if path=='/api/annex-a-controls/72/':return copy.deepcopy(self.control)
        return copy.deepcopy(self.records[int(path.strip('/').split('/')[-1])])
    def matching(self,marker):return [copy.deepcopy(r) for r in self.records.values() if marker in r.get('observations','')]
    def write(self,remote_id,payload):
        self.writes.append((remote_id,copy.deepcopy(payload)))
        key=remote_id or 10
        self.records[key]=dict(self.records.get(key,{}),**copy.deepcopy(payload),id=key,risk_code='RSK-10',controlled_score='12.00')
        if self.uncertain:raise UncertainWrite('Confirmación perdida')
        return copy.deepcopy(self.records[key])

class PublicationTests(TestCase):
    def setUp(self):
        folder=TemporaryDirectory();self.addCleanup(folder.cleanup)
        env=patch.dict(os.environ,PIMS_HISTORY_DB=str(Path(folder.name)/'history.sqlite3'))
        env.start();self.addCleanup(env.stop)
        self.gateway=FakeGateway()
        risk=dict(activo='ACT-1',amenaza='Falla de disco',vulnerabilidad='Sin prueba de restauración',consecuencia='Servicio interrumpido',
            referencias=[dict(fragmento_id='assets:1')],supuestos=['Caso ficticio'],informacion_faltante=['Acta'],
            estrategia='mitigar',responsable_propuesto='Operaciones',plazo_propuesto='30 días',acciones=['Probar restauración'],
            evidencia_a_solicitar=['Acta'],controles_ids=['annex-a-controls:72'],
            evaluacion=dict(estado='estimacion_propuesta',probabilidad=3,impacto=4,metodologia=from_gestitel(self.gateway.matrix).model_dump()))
        self.result=dict(fuente='gestitel',estado_respuesta='propuesta',riesgos=[risk],fuentes=[
            dict(id='assets:1',modulo='assets',texto=json.dumps(self.gateway.asset)),
            dict(id='annex-a-controls:72',modulo='annex-a-controls',texto=json.dumps(self.gateway.control))])
        self.key=history.save('riesgos','Evaluar',self.result)
    def prepare(self,target=None):return preview(self.key,0,target,gateway=self.gateway)
    def send(self,p,**kwargs):return confirm(p['id'],'Revisor de prueba',p['huella'],True,gateway=self.gateway,**kwargs)

    def test_preview_has_no_side_effects_and_approval_is_required(self):
        p=self.prepare()
        self.assertEqual(self.gateway.writes,[])
        self.assertEqual(p['datos']['assets'],[dict(asset='ACT-1')])
        self.assertEqual(p['datos']['treatments'][0]['annex_a_control'],'A.8.13')
        self.assertNotIn('residual_probability',p['datos'])
        for approval,fingerprint in [(False,p['huella']),(True,'wrong')]:
            with self.assertRaises(PublicationError):confirm(p['id'],'Revisor',fingerprint,approval,gateway=self.gateway)
        self.assertEqual(self.gateway.writes,[])

    def test_publish_verifies_remote_and_repeated_click_is_idempotent(self):
        p=self.prepare();receipt=self.send(p)
        self.assertEqual(receipt['id'],10)
        self.assertEqual(load_preview(p['id'])['state'],'published')
        self.assertEqual(self.send(p)['id'],10)
        second=self.prepare();self.send(second)
        self.assertEqual(len(self.gateway.writes),1)

    def test_stale_asset_matrix_or_period_prevent_write(self):
        for part in ('asset','matrix','period'):
            with self.subTest(part=part):
                self.gateway=FakeGateway();p=self.prepare()
                if part=='period':self.gateway.period['status']='C'
                else:getattr(self.gateway,part)['updated_at']='v2'
                with self.assertRaises(ValueError):self.send(p)
                self.assertEqual(self.gateway.writes,[])

    def test_uncertain_write_is_not_retried_and_can_be_reconciled(self):
        p=self.prepare();self.gateway.uncertain=True
        with self.assertRaises(UncertainWrite):self.send(p)
        self.assertEqual(load_preview(p['id'])['state'],'uncertain')
        with self.assertRaises(PublicationError):self.send(p)
        second=self.prepare()
        with self.assertRaises(PublicationError):self.send(second)
        self.assertEqual(len(self.gateway.writes),1)
        self.assertEqual(reconcile(p['id'],gateway=self.gateway)['id'],10)
        self.assertEqual(len(self.gateway.writes),1)

    def test_update_preserves_links_and_treatments_and_rejects_closed_risks(self):
        self.gateway.records[10]=dict(id=10,risk_code='RSK-10',period=1,status='O',assets=[dict(asset='ACT-1')],
            observations='Anterior',description='Anterior',treatments=[dict(description='Plan existente')])
        p=self.prepare(10)
        self.assertEqual(p['accion'],'actualizar')
        self.assertNotIn('assets',p['datos']);self.assertNotIn('treatments',p['datos'])
        self.send(p)
        self.assertEqual(self.gateway.records[10]['treatments'],[dict(description='Plan existente')])
        self.gateway.records[10]['status']='C'
        with self.assertRaises(PublicationError):self.prepare(10)

    def test_remote_changes_since_preview_prevent_update(self):
        self.gateway.records[10]=dict(id=10,period=1,status='O',assets=[dict(asset='ACT-1')],observations='')
        p=self.prepare(10);self.gateway.records[10]['description']='Otro usuario modificó el registro'
        with self.assertRaises(PublicationError):self.send(p)
        self.assertEqual(self.gateway.writes,[])

    def test_invalid_or_insufficient_scenarios_never_publish(self):
        with self.assertRaises(PublicationError):preview(self.key,True,gateway=self.gateway)
        with self.assertRaises(PublicationError):preview(self.key,0,True,gateway=self.gateway)
        self.result['riesgos'][0]['estrategia']='aceptar_propuesto'
        key=history.save('riesgos','Aceptar',self.result)
        with self.assertRaises(PublicationError):preview(key,0,gateway=self.gateway)

    def test_http_routes_reject_injected_payloads(self):
        client=app.test_client()
        with patch('src.priv_audit.publication.Gateway',return_value=self.gateway):
            self.assertEqual(client.post(f'/api/history/{self.key}/gestitel/preview',json={'indice':0,'payload':{}}).status_code,400)
            p=client.post(f'/api/history/{self.key}/gestitel/preview',json={'indice':0}).json
            url=f"/api/gestitel/previews/{p['id']}/confirm"
            self.assertEqual(client.post(url,json={'revisor':'Persona','huella':p['huella'],'confirmar':False}).status_code,409)
            self.assertEqual(client.post(url,json={'revisor':'Persona','huella':p['huella'],'confirmar':True}).status_code,200)
            self.assertEqual(client.get(f'/api/history/{self.key}').json['publicaciones'][-1]['state'],'published')

    def test_concurrent_previews_cannot_send_same_scenario(self):
        first=self.prepare();second=self.prepare()
        with history.connect() as db:
            db.execute("UPDATE gestitel_previews SET state='sending' WHERE id=?",(first['id'],))
        with self.assertRaises(PublicationError):self.send(second)
        self.assertEqual(self.gateway.writes,[])

    def test_mismatched_remote_receipt_stays_uncertain(self):
        original=self.gateway.write
        def write(remote_id,payload):
            result=original(remote_id,payload)
            self.gateway.records[result['id']]['description']='No coincide con aprobación'
            return result
        self.gateway.write=write
        p=self.prepare()
        with self.assertRaises(UncertainWrite):self.send(p)
        self.assertEqual(load_preview(p['id'])['state'],'uncertain')
        with self.assertRaises(UncertainWrite):reconcile(p['id'],gateway=self.gateway)
        self.assertEqual(len(self.gateway.writes),1)
