# Clear Node Modules and Reinstall

If you're experiencing persistent timeout errors or other issues, try clearing node_modules and reinstalling:

## For grc_frontend:

```bash
cd grc_frontend
rm -rf node_modules
rm -rf package-lock.json
npm cache clean --force
npm install
```

## For tprm_frontend:

```bash
cd grc_frontend/tprm_frontend
rm -rf node_modules
rm -rf package-lock.json
npm cache clean --force
npm install
```

## Windows PowerShell:

```powershell
# grc_frontend
cd grc_frontend
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm cache clean --force
npm install

# tprm_frontend
cd tprm_frontend
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm cache clean --force
npm install
```

## After clearing, restart dev server:

```bash
# Stop current server (Ctrl+C)
# Then restart
npm run serve
```















