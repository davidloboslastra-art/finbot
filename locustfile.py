from locust import HttpUser, task, between


class Usuario(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(3)
    def cuota(self):
        self.client.post("/chat", json={"mensaje": "cuota de 10 millones a 36 meses al 12%"})

    @task(2)
    def glosario(self):
        self.client.post("/chat", json={"mensaje": "qué es el CAE"})

    @task(1)
    def health(self):
        self.client.get("/health")
