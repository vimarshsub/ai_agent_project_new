# Deploying the AI Agent API on Koyeb

This guide provides instructions for deploying the AI Agent API on Koyeb, a developer-friendly serverless platform.

## Prerequisites

1. A [Koyeb account](https://app.koyeb.com/auth/signup)
2. Your code pushed to a GitHub repository
3. Environment variables set up (OpenAI API key, etc.)

## Deployment Steps

### 1. Using the Koyeb Web Interface

1. Log in to your [Koyeb account](https://app.koyeb.com/)
2. Click on "Create App"
3. Choose "GitHub" as the deployment method
4. Select your repository and branch (main)
5. Configure the build:
   - Runtime: Docker
   - Dockerfile path: `./Dockerfile`
   - Port: 8000
6. Add environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - Any other API keys or configuration needed by your agent
7. Choose region and instance type (Nano should be sufficient for testing)
8. Click "Deploy"

### 2. Using the Koyeb CLI

1. Install the Koyeb CLI:
   ```bash
   curl -fsSL https://cli.koyeb.com/install.sh | bash
   ```

2. Log in to Koyeb:
   ```bash
   koyeb login
   ```

3. Deploy your app:
   ```bash
   koyeb app init ai-agent-api \
     --git github.com/yourusername/ai_agent_project_new \
     --git-branch main \
     --ports 8000:http \
     --routes /:8000 \
     --env OPENAI_API_KEY=your_api_key_here \
     --instance-type nano \
     --region aws-us-east-1
   ```

4. Check deployment status:
   ```bash
   koyeb service get ai-agent-api
   ```

## Configuration Files

The repository includes the following configuration files for deployment:

- `Dockerfile`: Specifies how to build the container image
- `Procfile`: Defines the command to run the application
- `runtime.txt`: Specifies the Python version
- `koyeb.yaml`: Koyeb-specific configuration

## Testing Your Deployment

Once deployed, you can test your API with:

```bash
curl -X POST \
  https://your-app-name.koyeb.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how can you help me today?"}'
```

## Scaling

The default configuration uses a single instance. To scale:

1. In the Koyeb dashboard, go to your app
2. Click on "Edit" for the service
3. Modify the min/max instances under "Scaling"
4. Click "Update"

## Troubleshooting

- **Application crashes**: Check logs in the Koyeb dashboard
- **Slow responses**: Consider upgrading your instance type
- **Memory errors**: Check if the instance type provides enough memory for your application

## Cost Management

Koyeb charges based on resource usage. The Nano instance is cost-effective for light workloads. Monitor your usage in the Koyeb dashboard to avoid unexpected charges.

## Next Steps

- Set up CI/CD for automated deployments
- Configure a custom domain
- Implement monitoring and logging solutions 