const JsHttpRequest = {
  query: async function (url, data, callback) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(data)
      });

      const text = await response.text();
      let js = null;
      try {
        // Try to parse JSON from the server response
        js = JSON.parse(text);
      } catch (e) {
        console.error("Server did not return valid JSON", text);
      }

      callback(js, text);
    } catch (error) {
      console.error("Fetch error: ", error);
    }
  }
};
