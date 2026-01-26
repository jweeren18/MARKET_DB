# Contributing Guide

## Git Workflow

This project uses a **two-branch workflow** for development and production.

### Branches

#### `main` - Production Branch
- **Purpose**: Stable, production-ready code
- **Protection**: Should be protected (requires PR + review)
- **Deployment**: Automatically deployed to production
- **Direct commits**: ❌ Not allowed

#### `dev` - Development Branch
- **Purpose**: Active development and integration
- **Default for new features**: ✅ Yes
- **Testing**: All features tested here before merging to `main`
- **Direct commits**: ✅ Allowed for rapid development

### Workflow

#### 1. Daily Development (on `dev` branch)

```bash
# Make sure you're on dev
git checkout dev

# Pull latest changes
git pull origin dev

# Make your changes
# ... code, code, code ...

# Commit changes
git add .
git commit -m "feat: your feature description"

# Push to dev
git push origin dev
```

#### 2. Creating a Feature Branch (optional for larger features)

```bash
# Create feature branch from dev
git checkout dev
git checkout -b feature/your-feature-name

# Work on your feature
# ... code, code, code ...

# Commit and push
git add .
git commit -m "feat: implement your feature"
git push origin feature/your-feature-name

# Create PR: feature/your-feature-name → dev
```

#### 3. Deploying to Production (dev → main)

When `dev` is stable and ready for production:

```bash
# Make sure dev is up to date
git checkout dev
git pull origin dev

# Create a PR from dev to main on GitHub
# OR merge locally:
git checkout main
git pull origin main
git merge dev
git push origin main

# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Commit Message Convention

Use conventional commits for clear history:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks, dependencies
- `perf:` - Performance improvements

**Examples:**
```
feat: add opportunity scoring algorithm
fix: resolve database connection timeout
docs: update Airflow setup guide
chore: upgrade FastAPI to 0.110.0
```

### Branch Protection (Recommended)

On GitHub, configure branch protection for `main`:

1. Go to Settings → Branches
2. Add rule for `main` branch:
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass (CI/CD)
   - ✅ Require branches to be up to date
   - ✅ Include administrators (optional)

### Pull Request Process

1. **Create PR**: Always create a PR for `dev → main` merges
2. **Description**: Include what changed and why
3. **Testing**: Ensure all tests pass
4. **Review**: Self-review before merging (or get team review)
5. **Merge**: Use "Squash and merge" for clean history

### Hotfixes (Emergency Production Fixes)

For critical production bugs:

```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug-fix

# Fix the bug
# ... code ...

# Commit
git add .
git commit -m "fix: resolve critical production bug"

# Merge to main
git checkout main
git merge hotfix/critical-bug-fix
git push origin main

# Merge back to dev to keep in sync
git checkout dev
git merge hotfix/critical-bug-fix
git push origin dev

# Delete hotfix branch
git branch -d hotfix/critical-bug-fix
git push origin --delete hotfix/critical-bug-fix
```

### Current Development Status

🟢 **Active Development Branch**: `dev`
🔵 **Production Branch**: `main`

All new development should happen on `dev` or feature branches created from `dev`.

## Local Development Setup

See [README.md](README.md) for setup instructions.

## Questions?

If you have questions about the workflow, create an issue or discussion on GitHub.
