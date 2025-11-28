"""
Health check endpoint for Vercel
"""

def handler(request):
    """Health check endpoint"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": {
            "status": "healthy",
            "service": "bill-extraction",
            "version": "2.0.0"
        }
    }
