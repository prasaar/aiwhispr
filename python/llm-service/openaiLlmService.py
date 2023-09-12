import os
import sys
import logging
import openai
import time

curr_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(curr_dir)
os.getcwd()
sys.path.insert(1, os.path.abspath(os.path.join(curr_dir, os.pardir)))
sys.path.append("../base-classes")
sys.path.append("../llm-service")

from aiwhisprBaseClasses import baseLlmService

import logging

class createLlmService(baseLlmService):
   api_key:str
   model_name:str
  
   def __init__(self,llm_service_config):
      self.logger=logging.getLogger(__name__)
      baseLlmService.__init__(self, llm_service_config=llm_service_config, module_name='openaiLlmService')
      try:
        self.api_key = llm_service_config['llm-service-api-key']
        self.model_name = llm_service_config['model-name']
      except:
         self.logger.error("Could not set api-key, model-name for OpenAI using the configurations. Please ensure these are configured in the config file.")
         raise
             
   def connect(self):
      try:
        openai.api_key = self.api_key
      except:
        self.logger.error("Could not set api-key for OpenAI")

   def encode(self, in_text:str):
      
      continueTrying=True
      remainingAttempts=3
      sleepSeconds=5
      
      while continueTrying == True and remainingAttempts > 0:
        try:
          response_openai = openai.Embedding.create(
              model = self.model_name,
              input = in_text
          )
        except openai.error.APIError as e:
          continueTrying=False
          remainingAttempts=0
          self.logger.error("OpenAI API returned an APIError for encoding of {%s}", in_text)
          self.logger.exception(str(e))
        except openai.error.APIConnectionError as e:
          continueTrying=False
          remainingAttempts=0
          self.logger.error("OpenAI  returned an APIConnectionError for encoding of {%s}", in_text)
          self.logger.exception(str(e))
        except openai.error.RateLimitError as e:
          remainingAttempts=remainingAttempts-1
          self.logger.debug("RateLimitError : remaining attempts{%d} and will sleep for {%d} seconds",remainingAttempts, sleepSeconds)
          self.logger.error("OpenAI  returned RateLimitError for encoding of {%s}", in_text)
          self.logger.exception(str(e))
          if remainingAttempts > 0:
            time.sleep(sleepSeconds)
          else:
            continueTrying=False
          pass
        except openai.error.Timeout as e:
          remainingAttempts=remainingAttempts-1
          self.logger.debug("Timeout Error : remaining attempts{%d} and will sleep for {%d} seconds",remainingAttempts, sleepSeconds )
          self.logger.error("OpenAI  returned TimeoutError for encoding of {%s}", in_text)
          self.logger.exception(str(e))
          if remainingAttempts > 0:
            time.sleep(sleepSeconds)
          else:
            continueTrying=False
          pass
        except openai.error.InvalidRequestError as e:
          continueTrying=False
          remainingAttempts=0
          self.logger.error("OpenAI  returned InvalidRequestError for encoding of {%s}", in_text)
          self.logger.exception(str(e))
          pass
        except openai.error.AuthenticationError as e:
          continueTrying=False
          remainingAttempts=0
          self.logger.error("OpenAI  returned AuthenticationError for encoding of {%s}", in_text)
          self.logger.exception(str(e))
          pass
        except openai.error.ServiceUnavailableError as e:
          remainingAttempts=remainingAttempts-1
          self.logger.debug("ServiceUnavailableError : remaining attempts{%d} and will sleep for {%d} seconds",remainingAttempts, sleepSeconds )
          self.logger.error("OpenAI  returned ServiceUnavailableError for encoding of {%s}", in_text)
          self.logger.exception(str(e))
          if remainingAttempts > 0:
            time.sleep(sleepSeconds)
          else:
            continueTrying=False
          pass
        else: #success
          continueTrying=False
          remainingAttempts=0
      
      vector_embedding = response_openai['data'][0]['embedding']
      return vector_embedding