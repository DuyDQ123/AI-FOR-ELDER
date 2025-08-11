# System Power Control Documentation

## Overview

The power control system allows administrators and users to enable/disable the entire medicine dispensing system using either the admin web interface or a physical power button on the Raspberry Pi. When disabled, all medicine notifications, dispensing, and ESP32 alerts are suspended.

## System Components

### 1. Database Schema
- **Table**: `system_control`
- **Purpose**: Store system power status and change history
- **Location**: `database/system_control_schema.sql`

```sql
CREATE TABLE IF NOT EXISTS system_control (
    id INT AUTO_INCREMENT PRIMARY KEY,
    system_enabled BOOLEAN DEFAULT TRUE,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(50) DEFAULT 'system',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Flask API Endpoints

#### GET `/api/system_status`
- **Purpose**: Check current system power status
- **Authentication**: Requires API key
- **Response**: JSON with system status information
- **Used by**: ESP32, Raspberry Pi, Admin interface

#### POST `/api/system_control`
- **Purpose**: Update system power status (enable/disable)
- **Authentication**: Requires API key
- **Parameters**:
  - `action`: "enable" or "disable"
  - `source`: Source of the change (e.g., "admin_panel", "pi_button")
  - `notes`: Optional description
- **Used by**: Admin interface, Raspberry Pi

#### POST `/api/power_button_press`
- **Purpose**: Handle physical power button press from Raspberry Pi
- **Authentication**: Requires API key
- **Parameters**:
  - `user_id`: ID of user pressing button
  - `duration`: Button press duration in seconds
- **Behavior**: Toggles current system status
- **Used by**: Raspberry Pi power button handler

### 3. Raspberry Pi Implementation

#### Hardware Configuration
```python
PIN_POWER = 22  # GPIO pin for power button
```

#### Key Features
- **Power Button Detection**: GPIO interrupt handling with debounce protection
- **System Status Checking**: Periodic API calls to check system status
- **Schedule Suspension**: Skips medicine schedule checks when system disabled
- **Status Logging**: Records all power button events to admin logs

#### Code Integration
```python
def power_callback(self, channel):
    """Handle power button press to toggle system on/off"""
    # Debounce protection and system status toggle
    
def check_system_status(self):
    """Check system power status from server"""
    # API call to get current status
    
def schedule_loop(self):
    """Main schedule checking loop"""
    # Skip schedule checks if system disabled
```

### 4. ESP32 Implementation

#### System Status Monitoring
- **Frequency**: Checks system status every 15 seconds
- **Behavior**: Suspends all medicine notifications when disabled
- **Display**: Shows system status on TFT screen

#### Key Features
```cpp
bool systemEnabled = true;  // Track system power status
unsigned long lastSystemCheck = 0;
const unsigned long SYSTEM_CHECK_INTERVAL = 15000;  // 15 seconds

bool checkSystemStatus() {
    // API call to check system status
    // Update display if status changes
}
```

#### State Management
- **Disabled State**: Blocks all medicine confirmations and notifications
- **Status Display**: Visual indication of system power status
- **Automatic Sleep**: Forces sleep mode when system disabled

### 5. Admin Web Interface

#### Location
- **Template**: `templates/admin/system_power.html`
- **Route**: `/admin/system-power`
- **Access**: Admin users only

#### Features
- **Status Dashboard**: Real-time system status display
- **Manual Control**: Enable/Disable buttons
- **Activity Log**: Recent power control events
- **Auto-refresh**: Updates every 30 seconds

## Workflow Examples

### 1. Physical Power Button Press
```
1. User presses power button on Raspberry Pi (GPIO 22)
2. Raspberry Pi detects button press with debounce protection
3. Pi calls /api/power_button_press endpoint
4. Flask server toggles system status in database
5. Server logs action to admin_log table
6. ESP32 detects status change on next API check (15s)
7. ESP32 updates display and suspends/resumes operations
8. Admin interface shows updated status
```

### 2. Admin Web Control
```
1. Admin logs into web interface
2. Admin navigates to System Power Control page
3. Admin clicks Enable/Disable button
4. JavaScript calls /api/system_control endpoint
5. Flask server updates system status
6. Server logs admin action
7. Page refreshes to show new status
8. Raspberry Pi and ESP32 detect change on next check
```

### 3. System Disabled State
```
When system_enabled = FALSE:
- Raspberry Pi: Skips medicine schedule checks
- ESP32: Shows "SYSTEM DISABLED" on display
- ESP32: Blocks all medicine confirmation buttons
- Flask: /api/check_schedule returns empty (no schedules)
- Admin: Web interface shows red "DISABLED" status
```

## Configuration

### Database Setup
1. Execute the SQL schema: `database/system_control_schema.sql`
2. Default system status is ENABLED (TRUE)

### API Keys
- Update API key in all components:
  - `routes/main.py`: Server-side validation
  - `rpi_handler2.py`: Raspberry Pi authentication
  - `esp32_medicine_touch_rtos_power.ino`: ESP32 authentication

### GPIO Configuration (Raspberry Pi)
```python
PIN_POWER = 22  # Can be changed to any available GPIO pin
```

### Timing Configuration (ESP32)
```cpp
const unsigned long SYSTEM_CHECK_INTERVAL = 15000;  // 15 seconds
```

## Security Features

### 1. Authentication
- All API endpoints require valid API key
- Admin interface requires login with admin privileges

### 2. Logging
- All power control actions logged to `admin_log` table
- Includes timestamp, user, action, and details
- Visible in admin interface for audit trail

### 3. Debounce Protection
- Raspberry Pi: 2-second minimum between button presses
- ESP32: System status caching to prevent API spam

## Troubleshooting

### Common Issues

#### 1. Power Button Not Responding
- Check GPIO wiring (PIN_POWER = 22)
- Verify button is connected between GPIO 22 and GND
- Check Raspberry Pi logs for button press detection

#### 2. ESP32 Not Detecting Status Changes
- Verify WiFi connection
- Check API key configuration
- Monitor serial output for API call results

#### 3. Admin Interface Not Loading Status
- Check database connection
- Verify `system_control` table exists
- Check Flask server logs for errors

### Debug Commands

#### Check System Status (API)
```bash
curl -X GET "http://192.168.1.159:5000/api/system_status" \
     -H "X-API-Key: my-secret-key-2025"
```

#### Manual Status Change (API)
```bash
curl -X POST "http://192.168.1.159:5000/api/system_control" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: my-secret-key-2025" \
     -d '{"action": "disable", "source": "test", "notes": "Testing"}'
```

#### Check Database Status (MySQL)
```sql
SELECT * FROM system_control ORDER BY updated_at DESC LIMIT 5;
SELECT * FROM admin_log WHERE target_type = 'system_control' ORDER BY timestamp DESC LIMIT 10;
```

## Maintenance

### Regular Tasks
1. **Monitor Logs**: Check admin_log table for unusual power control activity
2. **Database Cleanup**: Archive old log entries periodically
3. **Status Verification**: Verify all components respond to status changes

### Updates
- When updating API keys, update all three components (Flask, Pi, ESP32)
- Test power control after any system updates
- Verify admin interface accessibility after Flask updates

## Integration Notes

### Future Enhancements
1. **Scheduled Power Control**: Automatic enable/disable at specific times
2. **Multiple Power Modes**: Different levels of system operation
3. **Remote Power Control**: SMS or mobile app integration
4. **Power Usage Monitoring**: Track system uptime and usage patterns

### Compatibility
- Compatible with existing medicine scheduling system
- Does not interfere with user accounts or medicine data
- Gracefully handles network disconnections
- Safe to enable/disable during active medicine notifications