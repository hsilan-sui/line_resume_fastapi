// src/middlewares/jobAuth.js

function requireJobToken(req, res, next) {
    const expected = process.env.NODE_JOB_TOKEN || "";
    const got = req.headers["x-job-token"] || "";
  
    if (!expected) {
      return res.status(500).json({ message: "NODE_JOB_TOKEN is not set" });
    }
  
    if (got !== expected) {
      return res.status(401).json({ message: "unauthorized" });
    }
  
    next();
  }
  
  module.exports = { requireJobToken };
  