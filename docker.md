### Docker Compose for the four terminal services

1. Make sure that the files .env files have the proper api keys , some variables will be overridden by docker compose. 
./backend/.env 
./lamb-kb-server-stable/.env  


The [docker-compose.yaml] file  will set up 4 containers:
- Open WebUI API (port 8080)
- LAMB KB server (port 9090)
- LAMB Backend (port 9099)
- Frontend Svelte dev server (port 5173)

The Docker setup uses bind mounts to the project directory at `/opt/lamb-project/lamb` with container-internal networking between services. You may adapt the file to your DNS configuration for production servers.


- Ensure `backend/.env` exists and includes a valid `OPENAI_API_KEY`. Container overrides set:
  - `OWI_BASE_URL=http://openwebui:8080`
  - `OWI_PATH=/opt/lamb-project/lamb/open-webui/backend/data`
  - `LAMB_DB_PATH=/opt/lamb-project/lamb`
- Ensure you have copied the `config.js` file
  - `cp /opt/lamb-project/lamb/frontend/svelte-app/static/config.js.sample /opt/lamb-project/lamb/frontend/svelte-app/static/config.js`
- Build the Frontend
  - Install nvm and then 
```
cd /opt/lamb-project/lamb/frontend/svelte-app
nvm use 20
npm install
npm run build
```  
- Start all services:
  - `docker compose up -d`
- Open:
  - Frontend: `http://localhost:5173`
  - Backend docs: `http://localhost:9099/docs`
  - KB docs: `http://localhost:9090/docs`
  - Open WebUI health: `http://localhost:8080/health`

- Stop:
  - `docker compose down`

- Logs:
  - `docker compose logs -f backend` (or `kb`, `openwebui`, `frontend`)

- Optional: if `frontend/static/config.js` points at localhost but you’re browsing from another machine, edit it to target your host IP.

- Node LTS and Python deps are installed inside containers at runtime; your host does not need nvm/uv installed for compose mode.

- Data persists via bind mounts under `/opt/lamb-project/lamb` (Open WebUI DB: `open-webui/backend/data/webui.db`, Chroma: `open-webui/backend/data/vector_db/chroma.sqlite3`, backend uses files under `/opt/lamb-project/lamb`).

- You can still run the four services natively; this compose file simply consolidates the terminal steps into containers.

- To rebuild node modules or Python deps after code changes, `docker compose restart frontend` or `docker compose restart backend` (or bring down/up).

- If you ever need to change ports, edit the published port mappings in this file.

- To run in foreground for dev logs: `docker compose up` without `-d`.

- To clean volumes, since we’re bind-mounting, the files live under `/opt/lamb-project/lamb` and won’t be removed by `down -v` unless you switch to named volumes.

- If `backend/requirements.txt` is heavy, consider building images instead of installing on start; for now, this mirrors your guide’s runtime installs.

- If Open WebUI needs additional envs, add them under the `openwebui` service environment block.

- For production, replace the frontend dev server with a built static site behind a web server; this compose is dev-focused.
