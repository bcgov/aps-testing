import os
from locust import HttpUser, between, task
import time
import random

class WaitingRoom:
    ticket = None
    time_bucket_start = int(time.time())
    time_buckets = dict()

    deferred_next_t = 0

    room = "ARD" # os.environ['ROOM']
    cookie_name = "WAITINGROOM" # os.environ['COOKIE_NAME']
    poll_url = "https://bcstats-waitroom.api.gov.bc.ca/Ticket" # os.environ['TICKET_POLL_URL']
    refresh_url = "https://bcstats-waitroom.api.gov.bc.ca/Ticket/check-in" # os.environ['TICKET_REFRESH_URL']
    redirect_path = "" # os.environ['REDIRECT_PATH']

    get_headers = {
    }

    headers = {
    "Content-Type": "application/json",
    }

    def get_cookie (self):
        cookies = {}
        if self.ticket is not None:
          cookies[self.cookie_name] = self.ticket["token"]
        return cookies

    def pass_through_waitroom(self, client):

      documents = [
        "/",
        "/main.css",
        "/main.js"
      ]


      try:
        # Go get all the static content
        for doc in documents:
          response = client.get("%s" % doc, headers=self.get_headers)

        busy = 0
        while True:
          # Ask for a ticket
          response = client.post("%s?room=%s" % (self.poll_url, self.room), headers = self.headers)


          # The waiting queue has exceeded maximum capacity, try again later
          if response.status_code == 503:
            busy = busy + 1
            print("[%d] Exceeded capacity - sleeping 10-20 seconds" % busy)
            wait_t = random.uniform(10, 20)
            time.sleep(wait_t)
          elif response.status_code == 429:
            busy = busy + 1
            wait_t = random.uniform(0, 4)
            print("[%d] Too Many Requests - sleeping %f seconds" % (busy, wait_t))
            time.sleep(wait_t)
          elif response.status_code != 200:
            busy = busy + 1
            wait_t = random.uniform(5, 10)
            print("[%d] Unknown Error %d - sleeping %f seconds" % (response.status_code, busy, wait_t))
            time.sleep(wait_t)
          else:
            ticket = response.json()

            attempts = 1
            while True:
              print(ticket["id"], ticket["status"], ticket["queuePosition"])

              if ticket["status"] == "Processed":
                # If processed, then redirect back with the set cookie
                cookies = {}
                cookies[self.cookie_name] = ticket["token"]

                time_bucket_end = int(time.time())
                bucket = "%d" % round((time_bucket_end - self.time_bucket_start) / 60, 0)
                if bucket in self.time_buckets:
                  self.time_buckets[bucket] = self.time_buckets[bucket] + 1
                else:
                  self.time_buckets[bucket] = 1

                #response = self.client.get("/onward", headers = headers, cookies = cookies)
                #response = self.client.get(redirect_path, headers = headers, cookies = cookies)

                print(self.time_buckets)

                self.ticket = ticket
                return True
              else:
                # else wait until next checkin time, to refresh the queue position
                attempts = attempts + 1

                wait_t = ticket["checkInAfter"] - time.time()
                print("[%d] Wait for %f seconds" % (attempts, wait_t))
                time.sleep(wait_t)

                data = {
                  "id": ticket["id"],
                  "nonce": ticket["nonce"],
                  "room": ticket["room"]
                }
                response = client.put("%s" % (self.refresh_url), json = data, headers = self.headers)
                response.raise_for_status()

                ticket = response.json()

      except BrokenPipeError:
          pass
      except Exception as ex:
        print("Wait Room Exception.. Sleep for a bit..")
        print(ex)
        time.sleep(5)
        raise ex

    def refresh_token(self, client):
        ticket = self.ticket

        wait_t = ticket["checkInAfter"] - time.time()
        print("Refresh Token", ticket["id"], wait_t)

        deferred_t = self.deferred_next_t - time.time()

        if wait_t > 0 or deferred_t > 0:
          return

        busy = 0

        data = {
            "id": ticket["id"],
            "nonce": ticket["nonce"],
            "room": ticket["room"]
        }
        response = client.put("%s" % (self.refresh_url), json = data, headers = self.headers)

        if response.status_code == 503:
            busy = busy + 1
            print("[%d] Exceeded capacity - sleeping 10-20 seconds" % busy)
            wait_t = random.uniform(10, 20)
            self.deferred_next_t = time.time() + wait_t
            # time.sleep(wait_t)
        elif response.status_code == 429:
            busy = busy + 1
            wait_t = random.uniform(0, 4)
            print("[%d] Too Many Requests - sleeping %f seconds" % (busy, wait_t))
            self.deferred_next_t = time.time() + wait_t
            # time.sleep(wait_t)
        elif response.status_code != 200:
            busy = busy + 1
            wait_t = random.uniform(5, 10)
            print("[%d] Unknown Error %d - sleeping %f seconds" % (response.status_code, busy, wait_t))
            self.deferred_next_t = time.time() + wait_t
            # time.sleep(wait_t)
        else:
            self.ticket = response.json()

