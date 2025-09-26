from deye_exceptions import DeyeKnownException

class EcoflowException(DeyeKnownException):
  """
  Base exception for all Ecoflow-related errors.

  This exception serves as the parent class for more specific 
  Ecoflow errors such as HTTP failures or invalid responses.
  """
  pass

class EcoflowHttpErrorException(EcoflowException):
  """
  Raised when an HTTP request to the Ecoflow API fails.

  This exception indicates network issues, timeouts, or 
  non-successful HTTP status codes returned by the API.
  """
  pass

class EcoflowResponseErrorException(EcoflowException):
  """
  Raised when the Ecoflow API returns an invalid or unexpected response.

  This may occur if the response JSON cannot be parsed, 
  required fields are missing, or the API signals an error condition.
  """
  pass
