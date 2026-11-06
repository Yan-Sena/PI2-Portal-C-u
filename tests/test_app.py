import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, cpf_valido  # noqa: E402

CPF_OK = "529.982.247-25"


class PortalTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app(self.path)
        self.c = self.app.test_client()

    def tearDown(self):
        os.remove(self.path)

    def test_cpf(self):
        self.assertTrue(cpf_valido(CPF_OK))
        self.assertFalse(cpf_valido("111.111.111-11"))
        self.assertFalse(cpf_valido("123"))

    def test_saude_e_pagina(self):
        self.assertEqual(self.c.get("/api/saude").get_json()["status"], "ok")
        r = self.c.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"CEU Aricanduva", r.data)

    def test_lista_avisos_e_eventos(self):
        self.assertEqual(len(self.c.get("/api/avisos").get_json()), 3)
        self.assertEqual(len(self.c.get("/api/eventos").get_json()), 3)

    def test_cadastro_valido_e_duplicado(self):
        body = {"nome": "Maria Silva", "cpf": CPF_OK, "consentimento": True}
        self.assertEqual(self.c.post("/api/municipes", json=body).status_code, 201)
        self.assertEqual(self.c.post("/api/municipes", json=body).status_code, 409)

    def test_cadastro_invalido(self):
        r = self.c.post("/api/municipes", json={"nome": "Maria", "cpf": "123", "consentimento": False})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.get_json()["erros"]), {"nome", "cpf", "consentimento"})

    def test_aviso_exige_token(self):
        novo = {"unidade": "Telecentro", "titulo": "Curso", "texto": "Inscrições abertas."}
        self.assertEqual(self.c.post("/api/avisos", json=novo).status_code, 401)
        h = {"X-Admin-Token": self.app.config["ADMIN_TOKEN"]}
        self.assertEqual(self.c.post("/api/avisos", json=novo, headers=h).status_code, 201)
        self.assertEqual(len(self.c.get("/api/avisos").get_json()), 4)
        self.assertEqual(self.c.post("/api/avisos", json={}, headers=h).status_code, 400)


if __name__ == "__main__":
    unittest.main()
