# Care Plan Generator

Automatically generate specialty-pharmacy care plans from patient clinical data.

See **[design_doc.md](./design_doc.md)** for product and technical design.

## Local setup

```bash
npm install
cp .env.example .env   # then add OPENAI_API_KEY
npx prisma migrate dev
npm run dev
```

## Documentation

| File | Description |
| --- | --- |
| [design_doc.md](./design_doc.md) | Design document (requirements, API, integrity rules) |
