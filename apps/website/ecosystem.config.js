module.exports = {
  apps: [{
    name: '0711-website',
    script: 'npm',
    args: 'run dev -- -p 4000',
    cwd: '/home/christoph.bertsch/0711/0711-OS/apps/website',

    // Auto-restart configuration
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s',
    max_memory_restart: '1G',

    // Restart delay (exponential backoff)
    restart_delay: 4000,

    // Error handling
    error_file: '/tmp/0711_website_error.log',
    out_file: '/tmp/0711_website_out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

    // Environment
    env: {
      NODE_ENV: 'development',
      PORT: 4000
    },

    // Watch for file changes (optional, can disable for production)
    watch: false,

    // Instance configuration
    instances: 1,
    exec_mode: 'fork'
  }]
};
