def flood_risk_alert(humidity, rain):
    """Simple flood risk prediction logic"""
    if rain > 50 or humidity > 85:
        return "🚨 High Flood Risk!"
    elif rain > 20:
        return "⚠️ Moderate Risk"
    else:
        return "✅ Safe Conditions"
