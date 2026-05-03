# Contributing Guide

Thank you for interest in contributing! This document explains how to contribute to the Handoff Dashboard project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### 1. Fork & Clone
```bash
git clone https://github.com/yourusername/handoff-dashboard.git
cd handoff-dashboard
```

### 2. Setup Development Environment
```bash
make setup
```

### 3. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Backend Development

#### Code Structure
```
backend/
├── app/
│   ├── adapters/        # Channel adapters
│   ├── models/          # Data models & schemas
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   └── main.py          # FastAPI app
├── requirements.txt     # Dependencies
├── run.py              # Entry point
└── Dockerfile          # Container configuration
```

#### Adding Features

1. **New Channel Adapter**
   ```python
   # backend/app/adapters/my_channel.py
   from app.adapters.base import BaseChannelAdapter
   
   class MyChannelAdapter(BaseChannelAdapter):
       def __init__(self):
           super().__init__("my_channel")
       
       def parse_incoming(self, payload):
           # Parse payload and return NormalizedMessage
           pass
       
       async def send_message(self, user_id, text):
           # Send message to user
           pass
   ```

2. **Register in Registry**
   ```python
   # backend/app/adapters/registry.py
   from app.adapters.my_channel import MyChannelAdapter
   
   # In _initialize_default_adapters():
   self.register_class("my_channel", MyChannelAdapter)
   ```

3. **Test It**
   ```bash
   curl -X POST http://localhost:8000/api/webhook/my_channel \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test", "text": "Hello"}'
   ```

#### Running Backend Tests
```bash
cd backend
python -m pytest tests/
```

#### Code Style
- Use Black for formatting: `black .`
- Use isort for imports: `isort .`
- Follow PEP 8
- Add type hints to functions

### Frontend Development

#### Code Structure
```
frontend/
├── public/          # Static assets
├── src/
│   ├── components/  # React components
│   ├── hooks/       # Custom hooks
│   ├── services/    # API & utilities
│   ├── App.js       # Main app component
│   └── index.js     # Entry point
├── package.json     # Dependencies
└── Dockerfile       # Container config
```

#### Adding Components

1. **New Component**
   ```jsx
   // frontend/src/components/MyComponent.jsx
   import React from 'react';
   import { Icon } from 'lucide-react';
   
   const MyComponent = ({ prop1, prop2 }) => {
     return (
       <div className="p-4 rounded-lg border">
         {/* Your component */}
       </div>
     );
   };
   
   export default MyComponent;
   ```

2. **Use in App**
   ```jsx
   import MyComponent from './components/MyComponent';
   
   // In your component:
   <MyComponent prop1="value" prop2={data} />
   ```

#### Running Frontend
```bash
cd frontend
npm install
npm start
```

#### Code Style
- Use functional components with hooks
- Use Tailwind CSS for styling
- Follow React best practices
- Add PropTypes/TypeScript if adding features

### Testing Changes

1. **Local Testing**
   ```bash
   make test
   ```

2. **Manual Testing**
   - Start services: `make start`
   - Send test message: `curl -X POST http://localhost:8000/api/webhook/mock ...`
   - Check frontend: http://localhost:3000
   - Verify in dashboard

3. **Docker Testing**
   ```bash
   make rebuild
   make test
   ```

## Submitting Changes

### 1. Commit Guidelines

Use conventional commits:
```
feat: add new WhatsApp feature
fix: resolve issue with message parsing
docs: update README with setup instructions
refactor: improve adapter registry
test: add tests for telegram adapter
```

### 2. Push Changes
```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

Provide:
- Clear description of changes
- Link to relevant issues
- Screenshots if UI changes
- Test results

## Code Review

Reviewers will check:
- ✅ Code follows style guide
- ✅ Tests pass
- ✅ Documentation updated
- ✅ No security issues
- ✅ Backwards compatibility

## Adding Documentation

### README Updates
- Update if core functionality changes
- Add examples for new features
- Document breaking changes

### API Documentation
- Docstrings for all endpoints
- Examples in comments
- Parameter descriptions

### Architecture Changes
- Update ARCHITECTURE.md
- Add diagrams if needed
- Explain rationale

## Performance Considerations

- Minimize database queries
- Use caching where appropriate
- Optimize WebSocket broadcasts
- Profile code before optimizing

## Security

- Don't commit secrets
- Validate all inputs
- Use type hints for validation
- Follow OWASP guidelines
- Document security implications

## Common Tasks

### Adding a New Endpoint

1. **Create route**
   ```python
   @router.get("/path")
   async def endpoint_name():
       """Endpoint description"""
       return {"data": "value"}
   ```

2. **Update docs**
   - Add to README API section
   - Add example usage

3. **Test**
   ```bash
   curl http://localhost:8000/api/path
   ```

### Fixing a Bug

1. **Create branch**
   ```bash
   git checkout -b fix/bug-description
   ```

2. **Add test that fails**
   - Test should demonstrate the bug
   - Run: `make test`

3. **Fix code**
   - Implement fix
   - Run: `make test` (should pass)

4. **Commit**
   ```bash
   git commit -m "fix: describe the bug fix"
   ```

### Refactoring Code

- Keep refactorings separate from feature work
- Don't change behavior
- All tests must pass
- Use meaningful variable names

## Getting Help

- Check existing issues
- Review ARCHITECTURE.md
- Look at similar code
- Ask in issues or discussions

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

## License

By contributing, you agree code is licensed under the same license as the project (MIT).

---

Thank you for contributing to make Handoff Dashboard better! 🎉
