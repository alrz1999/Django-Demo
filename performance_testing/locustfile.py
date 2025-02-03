import random

from locust import HttpUser, between, task, SequentialTaskSet


class AuthenticatedUserBehavior(SequentialTaskSet):

    def on_start(self):
        """ Register a new user and log in to obtain access token """
        self.username = f"user_{random.randint(1, 100000)}"
        self.password = "testpassword"

        self.signup()
        self.login()

    def signup(self):
        """ Sign up a new user """
        response = self.client.post("/account/signup/", json={
            "username": self.username,
            "password": self.password
        })
        if response.status_code in (200, 201):
            print(f"User {self.username} registered successfully.")
        else:
            print(f"User {self.username} registration failed: {response.status_code}")

    def login(self):
        """ Log in and obtain an access token """
        response = self.client.post("/account/login/", json={
            "username": self.username,
            "password": self.password
        })
        if response.status_code in (200, 201):
            self.token = response.json()['access']
            self.refresh_token = response.json()['refresh']
        else:
            self.token = None
            print(f"Login failed for user {self.username}: {response.status_code}")

    @task(2)  # Assign higher weight to listing content
    def list_content(self):
        """ Authenticated user lists content with pagination """
        if self.token is not None and type(self.token) is str:
            headers = {"Authorization": f"Bearer {self.token}"}
            page = random.randint(1, 10)
            page_size = random.choice([10, 20])
            response = self.client.get(f"/content/list/?page={page}&page_size={page_size}", headers=headers)
            if response.status_code in (200, 201):
                print(f"Content listed successfully for page {page}, page_size {page_size}")
            else:
                print(f"Failed to list content: {response.status_code}")

    @task(1)  # Add scores with lower weight
    def add_content_score(self):
        """ Authenticated user adds score to a random content """
        if self.token is not None and type(self.token) is str:
            headers = {"Authorization": f"Bearer {self.token}"}
            content_id = random.randint(1, 100)  # Assuming content IDs are between 1 and 100
            score = random.randint(1, 5)  # Simulating different score values
            response = self.client.post("/content/score/", json={
                "content": content_id,
                "score": score
            }, headers=headers)
            if response.status_code in (200, 201):
                print(f"Score {score} added to content {content_id}.")
            else:
                print(f"Failed to add score: {response.status_code}")

    @task(3)  # Simulate token refresh
    def refresh_token(self):
        """ Refresh the token when the session is long """
        if self.refresh_token is not None and type(self.refresh_token) is str:
            print(f"Attempting to refresh token: {self.refresh_token}")  # Debugging line
            response = self.client.post("/account/token/refresh/", json={
                "refresh": self.refresh_token
            })
            if response.status_code in (200, 201):
                self.token = response.json()['access']
            else:
                print(f"Failed to refresh token: {response.status_code}")

    def on_stop(self):
        """ Clean up after the user (e.g., log out if needed) """
        print(f"User {self.username} finished performance tests.")


# class UnauthenticatedUserBehavior(HttpUser):
#     """ Simulate unauthenticated user behaviors such as login failures or browsing without logging in """
#     wait_time = between(1, 5)
#
#     @task(2)
#     def invalid_login(self):
#         """ Simulate invalid login attempts """
#         self.client.post("/account/login/", json={
#             "username": "invaliduser",
#             "password": "wrongpassword"
#         })
#
#     @task(1)
#     def list_content_unauthenticated(self):
#         """ Unauthenticated user attempts to list content """
#         self.client.get("/content/list/")


class ReditApiUser(HttpUser):
    wait_time = between(1, 3)  # Simulate waiting time between tasks
    tasks = [AuthenticatedUserBehavior]
