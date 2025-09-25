-- Create user for automation system
CREATE USER IF NOT EXISTS automation_user IDENTIFIED BY 'secure_password_123';

-- Grant permissions
GRANT ALL PRIVILEGES ON job_automation.* TO automation_user;
GRANT SHOW DATABASES ON *.* TO automation_user;