module.exports = {
  plugins: {
    "posthtml-expressions": {
      locals: {
        API_URL: process.env.API_URL
          
      }
    }
  }
};
