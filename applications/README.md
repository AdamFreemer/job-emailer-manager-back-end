# Applications App

This is the core app for job application tracking:
- Job application management
- Email classification and processing
- Link discovery and analysis
- Application status tracking

## Key Models:
- `Application` - Job applications with status tracking
- `Email` - Classified emails linked to applications
- `DiscoveredLink` - Job links found in emails
- `DomainFilter` - User's allowed/blocked domains

## Key Features:
- Email categorization (PROSPECT_SINGLE, JOB_LINK_LIST, APPLICATION_RESPONSE)
- Job link extraction and analysis
- Application status workflow
- Daily digest generation