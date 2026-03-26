// Simple Vercel serverless function that returns health info
module.exports = (req, res) => {
  const env = process.env.FLASK_ENV || process.env.NODE_ENV || 'development'
  const response = {
    status: 'healthy',
    services: {
      database: 'unknown',
      cache: process.env.REDIS_URL ? 'configured' : 'unavailable',
      ml_model: process.env.MODEL_PATH ? 'ready' : 'unavailable',
      free_apis: 'configured',
      queue: process.env.REDIS_URL ? 'configured' : 'in-memory'
    },
    ml_model_info: null,
    timestamp: new Date().toISOString(),
    environment: env
  }

  res.status(200).json(response)
}
