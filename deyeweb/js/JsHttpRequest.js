const JsHttpRequest = {
  /**
   * Sends an asynchronous POST request with JSON data.
   * @param {string} url - The URL to send the request to.
   * @param {Object} data - The data to be stringified and sent in the request body.
   * @returns {Promise<Object>} A promise that resolves to the parsed JSON response.
   * @throws {Error} Throws an error if the HTTP response is not OK or if JSON parsing fails.
   */
  query: async function (url, data) {
    const response = await fetch(
      url,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data),
        credentials: 'include'
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP request returned error code ${response.status}`);
    }

    const text = await response.text();
    return JSON.parse(text);
  }
};
