# Brazil-Specific OSINT Resources

Brazilian public-record sources for OSINT investigations. Read this when the story is about Brazilian people, companies, or events.

This file complements (does not replace) the global tools in `tools-catalog.md`. Brazilian investigations almost always need *both* the global aggregators (OpenCorporates, OpenSanctions, Aleph) *and* the Brazilian primary sources, because the aggregators frequently lag the originals or miss state/municipal data

## Cadastros e dados corporativos

### Receita Federal — CNPJ
- **What:** Federal tax ID lookup for any Brazilian company.
- **URL:** https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/Cnpjreva_Solicitacao.asp
- **Pulls:** legal name, fantasy name, address, registration date, CNAE (economic activity), capital, partners (in some cases).
- **Bulk data:** Receita Federal publishes the full CNPJ database periodically. **Brasil.IO** (https://brasil.io/dataset/socios-brasil/) and **Casa dos Dados** (https://casadosdados.com.br/) provide more friendly interfaces.
- **Limits:** Beneficial-ownership transparency is partial. Use Receita's UBO declarations where available, then triangulate with state JUCESP-class registries.

### State commercial registries
- Each state has its own (Junta Comercial). For São Paulo: **JUCESP**. For Paraná: **JUCEPAR**. Etc.
- **Use for:** Filings, share transfers, statutory changes that may not yet appear in the federal CNPJ snapshot.
- **Limits:** Many state registries charge per document. Some require login or in-person retrieval.

### CEIS / CEPIM / CNEP — Cadastros de empresas sancionadas
- **CEIS** (Cadastro Nacional de Empresas Inidôneas e Suspensas): https://portaldatransparencia.gov.br/sancoes/ceis
- **CEPIM** (Empresas Punidas/Impedidas de contratar): same portal
- **CNEP** (Cadastro Nacional de Empresas Punidas): same portal
- **Use for:** Companies barred from federal contracting; basic anti-corruption screening.

### CGU — Portal da Transparência
- **URL:** https://portaldatransparencia.gov.br
- **Pulls:** federal salaries, pensions, contracts, sanctions, beneficiary lists for federal social programs
- **Brilliant for:** salary lookups for federal civil servants; verifying who got which contract; verifying social-program receipts.

### TCU — Tribunal de Contas da União
- Audit reports on federal spending; useful for context on procurement irregularities.
- URL: https://portal.tcu.gov.br

## Justiça e processos

### CNJ — Conselho Nacional de Justiça
- **DataJud / public dashboards** — aggregated court data
- URL: https://www.cnj.jus.br

### Tribunais
- Each court has its own portal. For most journalists, **JusBrasil** (https://www.jusbrasil.com.br) and **Escavador** (https://www.escavador.com) are the practical aggregators — note they have limits and paywalls. The original portals (TJSP, TJRJ, STJ, STF, TRFs, TRTs) are authoritative.

### MPF and state Ministério Público
- Public-action filings; sometimes broader than court records (ICs — inquéritos civis públicos).
- URL: https://www.mpf.mp.br

### Justiça Eleitoral — TSE
- **DivulgaCandContas** for candidate filings, asset declarations, campaign finance:
  - https://divulgacandcontas.tse.jus.br
- **Use for:** any politician profile. Always start here.

## Trabalho

### Lista Suja do Trabalho Escravo
- The Ministry's "dirty list" of employers caught using slave-like labour conditions.
- Critical for any investigation into supply chains, agriculture, construction.
- **Limits:** Only employers caught by inspection — many evade it.

### CAGED / RAIS (formal-employment statistics)
- For aggregate analysis, not individual lookup.

## Meio ambiente

### IBAMA — auto de infração / SICAFI
- Environmental fines and embargoes.
- URL: https://servicos.ibama.gov.br
- **Bulk data:** Periodically published; several newsrooms have open notebooks for analysis.

### ICMBio — embargoed areas
- Areas embargoed by ICMBio in conservation units.

### CAR — Cadastro Ambiental Rural
- Required for all rural properties; useful for tying landowners to specific tracts of land.
- URL: https://www.car.gov.br

### MapBiomas
- Land-use change time-series for any area in Brazil; deforestation alerts.
- URL: https://mapbiomas.org

### INPE / DETER / PRODES
- Official deforestation monitoring (INPE).
- URL: http://terrabrasilis.dpi.inpe.br

### Sigef / SNCI (INCRA)
- Geographic registry of rural properties; ownership.

## Segurança pública

### Atlas da Violência (IPEA + FBSP)
- Aggregated public-security data.

### Anuário Brasileiro de Segurança Pública (FBSP)
- Annual; granular per state.

### Disque-100 / Disque-180
- Reporting hotlines — data is partially published but not for individual lookups.

## Comunicação e mídia

### ANATEL
- Telecom licensees, broadcast concessions, beneficial ownership of broadcasters.
- Critical for media-ownership investigations.

### Cadastro Nacional de Doadores Eleitorais (TSE)
- Campaign donors. Open data via TSE.

## Compras públicas

### PNCP — Portal Nacional de Contratações Públicas
- All federal, state, and municipal procurement notices and contracts (2021+).
- URL: https://www.gov.br/pncp
- **Bulk data:** API available; has been used in Brazilian investigative journalism projects on procurement irregularities and AI/surveillance contracts.

### ComprasNet (legacy federal)
- Pre-PNCP federal procurement.

### Estados e municípios
- Each state and large city has its own procurement portal. Coverage varies.

## Aggregators and journalist tools

### CruzaGrafos
- Network analysis on 89M+ Brazilian public records (corporate, electoral, judicial, sanctions).
- Used by 50+ Latin American newsrooms.

### Brasil.IO
- Open data aggregator: socios CNPJ, COVID-19 data, eleições, Diários Oficiais, gastos parlamentares, more.
- URL: https://brasil.io

### Querido Diário (Open Knowledge Brasil)
- Aggregated municipal Diários Oficiais — searchable.
- URL: https://queridodiario.ok.org.br

### Achados e Pedidos (Open Knowledge Brasil)
- Public collection of FOIA requests and responses. Useful for finding requests already made by other journalists.
- URL: https://achadosepedidos.org.br

### Hemeroteca Digital — Biblioteca Nacional
- Historical Brazilian newspapers, free, OCR'd.
- URL: https://bndigital.bn.gov.br/hemeroteca-digital

### LeIA / Atos Normativos
- Federal legislation tracking; multiple aggregators.

## Câmara e Senado APIs

### Dados Abertos da Câmara dos Deputados
- Open API: bills, votes, expenses, attendance, committees.
- URL: https://dadosabertos.camara.leg.br

### Dados Abertos do Senado Federal
- Open API: bills, votes, senators' expenses (CEAPS).
- URL: https://www12.senado.leg.br/dados-abertos

## Geolocalização brasileira

For Brazilian-specific geolocation:

- **License plates** — Brazilian Mercosul format (3 letters + digit + letter + 2 digits, since 2019); old format is 3 letters + 4 digits. State assignment (first letter cluster) used to indicate state of registration; Mercosul plates are *not* state-coded.
- **Phone numbers** — +55 country code; 11 / 21 / 31 etc. are city/area codes
- **Bus liveries** — São Paulo's SPTrans colours, Rio's BRT colours, etc., are highly characteristic
- **Architecture** — colonial styles cluster in NE coast (Salvador, Recife, Olinda); modernist in Brasília; eclectic in São Paulo; gauchao styles in RS
- **Vegetation** — Atlantic Forest vs Cerrado vs Amazônia vs Caatinga vs Pantanal vs Pampa — climate-zone fingerprint

## Notas finais

- The federal data ecosystem in Brazil is one of the strongest in Latin America, but state and municipal coverage is uneven. Cross-checking aggregators with original portals catches gaps.
- For grant-funded investigations, document data provenance carefully — funders increasingly ask for it.
