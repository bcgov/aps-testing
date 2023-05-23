# > locust
# > locust --config ./master.local.conf
from locust import HttpUser, task, between
from locust.exception import CatchResponseError
import time
import random
from bs4 import BeautifulSoup
from waitingroom import WaitingRoom

# roster survey
pages_roster = [
{
  "_cetecran":"INTRO",
  "zeroxaffichees": "INTRO"
},
{
  "_cetecran":"INTRO2"
},
{
  "_cetecran":"Q1HH",
  "ADDR_MADDR1":"1 Money Street",
  "ADDR_MADDR2":"Unit S",
  "ADDR_MCITY":"Cape Money",
  "ADDR_MPOSTAL_CODE":"S9S 9S9",
},
{
  "_cetecran":"Q2",  
  "AW2HH_C": "0",
  "AW2HH_Y": "0",
  "AW2HH_A": "1",
},
{
  "_cetecran": "Q2INTRO",
  "AFIRSTNAME01": "&#1455;&#1426;&#146F;&#14C7;&#1506;",
  "ALASTNAME01": "Money"
}
]

# household survey
pages_hh = [
  {
    "_cetecran": "Q1INTRO",
    "Q1INTRO": "1"
  },
  {
   "_cetecran": "QINSTRUCTIONS"
  },
  {
   "_cetecran": "Q4VERI"
  },
  {
   "_cetecran": "Q7VERI",
   "AQ7YEARVERI": "1990",
   "AQ7MONTHVERI": "01",
   "AQ7DAYVERI": "01",
   "AQ8AGEVERI": "33"
  },
  {
   "_cetecran": "Q9VERI"
  },
  {
   "_cetecran": "Q13ETHNICITY"
  },
  {
   "_cetecran": "Q14INDIG",
   "Q14INDIG": "4"
  },
  {
   "_cetecran": "Q19INDIG",
   "Q19INDIG": "2"
  },
  {
   "_cetecran": "Q15MEMINDIG",
   "Q15MEMINDIG": "2"
  },
  {
   "_cetecran": "Q21ANCES",
   "Q21ANCES": "2"
  },
  {
   "_cetecran": "Q22ANCES2",
   "Q22ANCES2": "21"
  },
  {
   "_cetecran": "Q23PLACE",
   "Q23PLACE": "1",
   "AQ23PLACE_BC": "Money Island"
  },
  {
   "_cetecran": "Q24PLACE",
   "Q24PLACE": "3",
   "AQ24PLACE_BC": "Money House"
  },
  {
   "_cetecran": "Q25CITIZ",
   "Q25CITIZ": "1"
  },
  {
   "_cetecran": "Q29LANG",
   "Q29LANG": "2"
  },
  {
   "_cetecran": "Q29ALANG",
   "Q29ALANG": "1"
  },
  {
   "_cetecran": "Q30RELIG",
   "Q30RELIG": "99"
  },
  {
   "_cetecran": "Q31RELIG",
   "Q31RELIG": "4"
  },
  {
   "_cetecran": "Q32RACE",
   "Q32RACE": "105"
  },
  {
   "_cetecran": "Q34CULTUREINTRO",
   "AQ34CULTURE_A": "Canadian"
  },
  {
   "_cetecran": "GO_TO_P1"
  },
  {
   "_cetecran": "Q41GEN",
   "Q41GEN": "1"
  },
  {
   "_cetecran": "Q40AGEN",
   "Q42GEN": "3"
  },
  {
   "_cetecran": "Q42GEN",
   "Q42GEN": "1"
  },
  {
   "_cetecran": "Q43GEN",
   "Q43GEN": "4"
  },
  {
   "_cetecran": "Q44FAM",
   "Q44FAM": "2"
  },
  {
   "_cetecran": "Q45FAM",
   "Q45FAM": "2"
  },
  {
   "_cetecran": "Q47EDU",
   "Q47EDU": "6"
  },
  {
   "_cetecran": "Q48INC",
   "Q48INC": "2"
  },
  {
   "_cetecran": "Q50INC",
   "Q50INC": "100"
  },
  {
   "_cetecran": "Q54DISAB",
   "Q54DISAB": "1"
  },
  {
   "_cetecran": "Q55DISAB",
   "Q55DISAB": "1"
  },
  {
   "_cetecran": "GO_TO_P2",
   "_proj": "cw241198_sandbox_test_p3"
  },
  {
   "_cetecran": "Q36MID",
   "Q36MID": "3",
   "_proj": "cw241198_sandbox_test_p3"
  },
  {
   "_cetecran": "Q37MID",
   "Q37MID": "3",
   "_proj": "cw241198_sandbox_test_p3"
  },
  {
   "_cetecran": "Q39MID",
   "Q39MID": "1",
   "_proj": "cw241198_sandbox_test_p3"
  },
  {
   "_cetecran": "Q055_21",
   "Q055_21": "1",
   "_proj": "cw241198_sandbox_test_p3"
  },
  {
   "_cetecran": "Q056_21",
   "ARESPTEL": "6043627851",
   "_proj": "cw241198_sandbox_test_p3"
  },
  {
   "_cetecran": "QCONC",
   "_next_question": "Submit",
   "_proj": "cw241198_sandbox_test_p3"
  },
  {
   "_cetecran": "THANKYOU",
   "_next_question": "Submit",
   "_proj": "cw241198_sandbox_test_p3"
  },
]

# import logging
# from http.client import HTTPConnection  # py3

# log = logging.getLogger('urllib3')
# log.setLevel(logging.DEBUG)

# # logging from urllib3 to console
# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
# log.addHandler(ch)

# HTTPConnection.debuglevel = 1

def wait_tm ():
  # do it for a 10 min survey
  return random.uniform(10, 15)
  # do it fast
  #return random.uniform(2, 4)

def wait_retry ():
  return random.uniform(1, 3)

class HelloWorldUser(HttpUser):
    #wait_time = between(200000000, 200000000)
    wait_time = between(0, 0)

    @task
    def post_survey(self):
      # self.client.keep_alive = False
      # self.client.keepalive = False
      # self.client.alive = False

      headers = {
      #  "Connection": "close"
      }

      wait_room = WaitingRoom()
      wait_room.pass_through_waitroom(self.client)
      cookies = wait_room.get_cookie()


      try:
        project = "cw241198_roster_test"
        # send GET to survey to generate the _telkey (unique identifier)
        response = self.client.get("/i/cwx.cgi?_proj=%s" % project, headers = headers, cookies = cookies)
        while response.status_code >= 400:
          time.sleep(wait_retry())
          response = self.client.get("/i/cwx.cgi?_proj=%s" % project, headers = headers, cookies = cookies)

        soup = BeautifulSoup(response.text, features="html.parser")
        cedossier = soup.find(id='_cedossier').get("value")

        # _telkey is stored in the cookies
        chocolateChip = response.cookies
        print('---------------')
        print(chocolateChip.get_dict())

        telkey = chocolateChip.get_dict()[project]

        cookies = wait_room.get_cookie()
        chocolateChip['WAITINGROOM'] = cookies['WAITINGROOM']

        print('telkey %s, cedossier %s' % (telkey, cedossier))
        
        index_roster = 0

        # complete the roster survey
        for index, page in enumerate(pages_roster):
          
          wait_room.refresh_token(self.client)
          cookies = wait_room.get_cookie()
          chocolateChip['WAITINGROOM'] = cookies['WAITINGROOM']

          data = {
              "_telkey": telkey,
              "_cedossier": cedossier,
              "_proj": project,
              "_cycle": "2",
              "_lang": "EN",
              "_javascript": "1",
              "_next_question": "Next"
          }

          for key in page.keys():
            data[key] = page[key]

          # Needs to be Tuples so that it can be passed to "files=" for multipart/form-data
          for key in data.keys():
            data[key] = (None, data[key])
          
          response = self.client.post("/i/cwx.cgi?page=%02d" % (index+1), cookies = chocolateChip, files=data, headers = headers)

          while response.status_code >= 400:
            time.sleep(wait_retry())
            response = self.client.post("/i/cwx.cgi?page=%02d" % (index+1), cookies = chocolateChip, files=data, headers = headers)

          wait_t = wait_tm()
          print("%s : %s - now wait %s seconds" % (index+1, response, wait_t))

          index_roster = index+1
          time.sleep(wait_t)
      
        # get the next survey link from page _cetecran = Q2INTROCONF
        #   <a href="cwx.cgi?_crypt=<string>" class="BUTTONsmall" target="_self">Begin First Name's survey</a>
        # <a href="cwx.cgi?_crypt=" class="BUTTONsmall" target="_self">Begin First name's survey</a>
        # lxml parser required for getting the URL here -- html.parser doesn't work here
        soup = BeautifulSoup(response.text, 'lxml')
        hh_survey = soup.find('a', class_='BUTTONsmall', href=True).get("href")
        
        # now complete the household survey
        response = self.client.get("/i/%s" % hh_survey, cookies = chocolateChip, name = "start_household_survey")
        
        while response.status_code >= 400:
          time.sleep(wait_retry())
          response = self.client.get("/i/%s" % hh_survey, cookies = chocolateChip, name = "start_household_survey_retry")


        # get new cedossier, telkey for new survey
        soup = BeautifulSoup(response.text, features="html.parser")
        # project = "cw241198_sandbox_test_p1"
        cedossier = soup.find(id='_cedossier').get("value")
        telkey = soup.find(id='_telkey').get("value")
        project = soup.find(id='_proj').get("value")

        print('telkey %s, cedossier %s, proj %s' % (telkey, cedossier, project))

        for index, page in enumerate(pages_hh):
          
          wait_room.refresh_token(self.client)
          cookies = wait_room.get_cookie()
          chocolateChip['WAITINGROOM'] = cookies['WAITINGROOM']

          data = {
              "_telkey": telkey,
              "_cedossier": cedossier,
              "_proj": project,
              "_cycle": "2",
              "_lang": "EN",
              "_javascript": "1",
              "_next_question": "Next"
          }

          for key in page.keys():
            data[key] = page[key]

          # Needs to be Tuples so that it can be passed to "files=" for multipart/form-data
          for key in data.keys():
            data[key] = (None, data[key])
          
          response = self.client.post("/i/cwx.cgi?page=%02d-%02d-%s" % (index_roster, index+1, page["_cetecran"]), cookies = chocolateChip, files=data, headers = headers)

          while response.status_code >= 400:
            time.sleep(wait_retry())
            response = self.client.post("/i/cwx.cgi?page=%02d-%02d-%s" % (index_roster, index+1, page["_cetecran"]), cookies = chocolateChip, files=data, headers = headers)

          soup = BeautifulSoup(response.text, features="html.parser")
          _cetecran = soup.find(id='_cetecran').get("value")

          if _cetecran == page["_cetecran"]:
            raise CatchResponseError("Page is not what is expected! %s %s" % ( _cetecran, page["_cetecran"]))

          project = soup.find(id='_proj').get("value")

          wait_t = wait_tm()
          print("%s : [%s] %s - now wait %s seconds" % (index_roster+index+1, _cetecran, response, wait_t))

          time.sleep(wait_t)

        # stop locust
        # only want to create one record
        #self.environment.runner.quit()

      except BrokenPipeError:
          pass
      except Exception as ex:
          print("Exception.. Sleep for a bit..")
          print(ex)
          #print(response.text)
          time.sleep(10)
          raise ex

