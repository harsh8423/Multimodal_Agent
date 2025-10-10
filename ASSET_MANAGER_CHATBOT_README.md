# Asset Manager Chatbot

## Overview

The Asset Manager Chatbot is an AI-powered assistant integrated into the asset-manager page that helps users manage their social media assets through natural language interactions. It provides a modern, conversational interface for CRUD operations on brands, competitors, templates, and data scraping.

## Features

### 🤖 AI Assistant Interface
- **Modern Chat UI**: Clean, responsive chat interface with real-time messaging
- **Quick Actions**: Pre-defined action buttons for common tasks
- **Real-time Connection**: WebSocket-based communication with connection status indicators
- **Typing Indicators**: Visual feedback when the AI is processing requests

### 🏢 Brand Management
- **Create Brands**: Set up new brands with name, description, website, and industry
- **Update Brands**: Modify existing brand information
- **Delete Brands**: Remove brands with confirmation
- **View Brands**: Retrieve and search through brand data

### 👥 Competitor Management
- **Add Competitors**: Track competitors across different social media platforms
- **Update Competitors**: Modify competitor information and metrics
- **Delete Competitors**: Remove competitors from tracking
- **Platform Support**: Instagram, LinkedIn, YouTube, and more

### 📝 Template Management
- **Create Templates**: Build content templates for different platforms
- **Update Templates**: Modify existing template content and metadata
- **Delete Templates**: Remove unused templates
- **Template Types**: Support for various content types (posts, reels, carousels, etc.)

### 🔍 Data Scraping
- **Single Competitor Scraping**: Scrape data from individual competitors
- **Bulk Scraping**: Perform batch scraping operations across multiple competitors
- **Scraping Analytics**: View scraping results and engagement metrics

## Technical Implementation

### Frontend Components

#### AssetManagerChatbot.js
- **WebSocket Integration**: Real-time communication with backend
- **Message Handling**: Process and display chat messages
- **Quick Actions**: Pre-defined prompts for common tasks
- **Connection Management**: Handle connection states and reconnection

#### Enhanced Asset Manager Page
- **Tab-based Interface**: AI Assistant as the primary tab
- **Modern UI Design**: Gradient headers and improved visual hierarchy
- **Responsive Layout**: Mobile-friendly design with adaptive stats display

### Backend Integration

#### Asset Agent Enhancement
- **Extended Capabilities**: Added CRUD operations to existing asset_agent
- **Natural Language Processing**: Conversational interface for asset management
- **Tool Integration**: Direct API calls to existing CRUD endpoints

#### New CRUD Tools
- **asset_crud_operations.py**: Comprehensive CRUD operations for all asset types
- **API Integration**: Direct calls to existing FastAPI endpoints
- **Error Handling**: Robust error handling and user feedback

#### System Configuration
- **Updated system_prompts.json**: Enhanced asset_agent with CRUD capabilities
- **Tool Registration**: Added new tools to tool_router.py
- **Schema Definitions**: Complete input/output schemas for all operations

## Usage Examples

### Creating a Brand
```
User: "I want to create a new brand called TechCorp"
Assistant: "I'd be happy to help you create a new brand! I'll need some information:
- Brand name: TechCorp
- Description: (optional)
- Website: (optional)
- Industry: (optional)

What description would you like to add for TechCorp?"
```

### Adding a Competitor
```
User: "Add a competitor from Instagram"
Assistant: "I'll help you add a new competitor! Please provide:
- Competitor name
- Instagram username/handle
- Description (optional)

What's the name of the competitor you'd like to track?"
```

### Scraping Data
```
User: "Scrape data from my competitors"
Assistant: "I can help you scrape competitor data! I can scrape from:
- Individual competitors (specify which one)
- All competitors at once
- Specific platforms

Which competitors would you like me to scrape data from?"
```

## Quick Actions

The chatbot provides quick action buttons for common tasks:

- 🏢 **Create a new brand** - Set up a new brand profile
- 👥 **Add a competitor** - Track a new competitor
- 📝 **Create a template** - Build a content template
- 🔍 **Scrape competitor data** - Collect competitor insights
- 📊 **Show my assets overview** - View all assets summary
- ✏️ **Update existing asset** - Modify existing assets

## API Endpoints Used

The chatbot integrates with existing API endpoints:

### Brands
- `POST /api/brands/` - Create brand
- `PUT /api/brands/{id}` - Update brand
- `DELETE /api/brands/{id}` - Delete brand
- `GET /api/brands/` - List brands

### Competitors
- `POST /api/competitors/` - Create competitor
- `PUT /api/competitors/{id}` - Update competitor
- `DELETE /api/competitors/{id}` - Delete competitor
- `GET /api/competitors/` - List competitors

### Templates
- `POST /api/templates/` - Create template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template
- `GET /api/templates/` - List templates

### Scraping
- `POST /api/competitors/{id}/scrape` - Scrape competitor
- `POST /api/scraping/scrape/batch` - Bulk scraping

## Installation & Setup

1. **Frontend Dependencies**: Ensure all React dependencies are installed
2. **Backend Tools**: The new CRUD tools are automatically registered
3. **WebSocket Connection**: Configure WebSocket URL in environment variables
4. **Authentication**: Ensure proper authentication tokens are available

## Future Enhancements

- **Voice Input**: Add speech-to-text capabilities
- **File Uploads**: Support for brand logos and media files
- **Advanced Analytics**: Enhanced reporting and insights
- **Bulk Operations**: Multi-select and batch operations
- **Export Features**: Export data to various formats
- **Integration**: Connect with external social media APIs

## Troubleshooting

### Connection Issues
- Check WebSocket URL configuration
- Verify authentication tokens
- Ensure backend services are running

### Tool Errors
- Verify API endpoint availability
- Check user permissions
- Review error logs for detailed information

### UI Issues
- Clear browser cache
- Check for JavaScript errors
- Verify responsive design on different screen sizes