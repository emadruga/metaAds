# Legal Compliance - Brazilian Electoral Law (TSE)

## Document Purpose

This document outlines the legal protections and compliance measures for storing and analyzing political advertising data collected from Meta Ad Library, specifically addressing Brazilian Electoral Law and TSE (Tribunal Superior Eleitoral) regulations.

---

## Legal Framework

### Data Source: Meta Ad Library Public API

All political advertising data in this system is collected from:
- **Source:** Meta Ad Library Public API
- **Access Method:** Official API with approved credentials
- **Data Status:** Publicly available information
- **Purpose:** Research, competitive intelligence, and electoral transparency

### Brazilian Legal Context

**TSE Regulatory Authority:**
- TSE (Tribunal Superior Eleitoral) regulates political advertising in Brazil
- TSE has authority to order removal of ads violating electoral law
- Violations include: false information, unauthorized content, illegal campaign practices

**Law 9.504/97 (Electoral Law) and Resolution TSE 23.610/2019:**
- Regulates political advertising during election periods
- Establishes content restrictions and disclosure requirements
- Defines penalties for violations

---

## Legal Risk Assessment

### Your Legal Position: PROTECTED ✅

**You are NOT liable for:**
1. ❌ Creating the political ad (you didn't create it)
2. ❌ Publishing/distributing the ad (Meta published it, you archived it)
3. ❌ Violating electoral law through the ad content (the advertiser/campaign is responsible)
4. ❌ Defying TSE removal orders (Meta must comply, not data collectors)

**Your Activity:**
- ✅ Collecting publicly available data from an official API
- ✅ Archiving for research and analysis purposes
- ✅ Private database for competitive intelligence
- ✅ Similar to journalistic archiving or academic research

### Legal Precedent & Analogies

**Protected Activities:**
- 📰 Journalists archiving political content (even if later removed)
- 🎓 Academic researchers studying campaign strategies
- 📊 Market research firms analyzing advertising trends
- 🏛️ Electoral transparency organizations documenting campaign activities
- 📚 Internet Archive preserving historical web content

**Legal Principle:**
> "Archiving publicly available information for research, documentation, and
> transparency purposes is protected activity, distinct from the original
> publication or distribution of content."

---

## Protection Measures Implemented

### 1. Data Source Attribution ✅

All data clearly attributed to Meta Ad Library:
```
Data Source: Meta Ad Library Public API (https://www.facebook.com/ads/library)
Collection Method: Official API with approved access
Legal Basis: Public information for transparency and research
```

### 2. Purpose Statement ✅

Clear statement of legitimate use:
```
Purpose: Competitive intelligence, market research, and electoral transparency
Use Case: Private analysis and internal reporting
Distribution: Non-public, research-only access
```

### 3. No Active Redistribution ✅

**System Design:**
- Private database (not publicly accessible)
- Internal analysis tools only
- Reports focus on aggregated data and trends
- No public website republishing individual ads
- No social media redistribution of ad content

### 4. Disclaimer in All Documentation ✅

```
═══════════════════════════════════════════════════════════════
AVISO LEGAL - LEGAL NOTICE
═══════════════════════════════════════════════════════════════

PORTUGUÊS:
Os dados de anúncios políticos contidos neste sistema foram coletados
da API pública do Meta Ad Library exclusivamente para fins de:
- Pesquisa de mercado
- Inteligência competitiva
- Análise de tendências eleitorais
- Transparência democrática

A presença de um anúncio neste banco de dados NÃO constitui:
- Endosso do conteúdo
- Republicação ou redistribuição ativa
- Violação de ordens de remoção do TSE

Anúncios removidos pela plataforma Meta ou pelo Tribunal Superior
Eleitoral (TSE) permanecem no histórico APENAS para fins de:
- Registro histórico e arquivamento
- Análise retrospectiva de estratégias
- Estudos de conformidade eleitoral
- Pesquisa acadêmica e jornalística

Este sistema é utilizado exclusivamente para análise interna e privada,
sem redistribuição pública de conteúdo político.

Base Legal:
- Constituição Federal (Art. 5º, XIV - acesso à informação)
- Lei 12.527/2011 (Lei de Acesso à Informação)
- Lei 9.504/97 (Lei Eleitoral)
- Atividade de pesquisa e transparência protegida

═══════════════════════════════════════════════════════════════

ENGLISH:
Political advertising data in this system was collected from the Meta Ad
Library public API exclusively for purposes of:
- Market research
- Competitive intelligence
- Electoral trend analysis
- Democratic transparency

The presence of an ad in this database does NOT constitute:
- Endorsement of content
- Republication or active redistribution
- Violation of TSE removal orders

Ads removed by Meta platform or by the Brazilian Electoral Court (TSE)
remain in the historical record ONLY for purposes of:
- Historical archiving and documentation
- Retrospective strategy analysis
- Electoral compliance studies
- Academic and journalistic research

This system is used exclusively for private internal analysis, without
public redistribution of political content.

Legal Basis:
- Brazilian Constitution (Art. 5º, XIV - right to information)
- Law 12.527/2011 (Freedom of Information Act)
- Law 9.504/97 (Electoral Law)
- Protected research and transparency activity

═══════════════════════════════════════════════════════════════
```

### 5. Removal Status Tracking (Recommended Enhancement)

**Database Schema Enhancement:**
```python
# Track removal status for compliance
removal_status = Column(String(50))
# Values: 'active', 'removed_by_platform', 'removed_by_tse', 'unknown'

removal_date = Column(DateTime, nullable=True)
last_verified = Column(DateTime, nullable=True)
tse_compliance_note = Column(Text, nullable=True)
```

**Periodic Verification:**
- Check if ads still exist in Meta Ad Library
- Mark removed ads with appropriate status
- Maintain historical record with removal context
- Document that removal was compliance with platform/TSE orders

---

## Risk Mitigation Strategies

### Strategy 1: Private Research Database ✅ IMPLEMENTED

**Current Status:** Your database is private and for internal research
- No public API exposing ad data
- No public website showing individual ads
- Access restricted to authorized researchers/analysts

**Risk Level:** **VERY LOW** ✅

### Strategy 2: Aggregate Reporting Only (Recommended)

When sharing findings:
- ✅ Share statistics and trends
- ✅ Share anonymized patterns
- ✅ Share aggregated insights
- ❌ Don't republish full ad content publicly
- ❌ Don't create searchable public database of removed ads

**Example Safe Report:**
```
"During the 2026 presidential campaign, we observed 1,247 political ads
mentioning healthcare policy. Of these, 3% were removed by the platform,
with removal rates highest in the final week before the election."
```

### Strategy 3: Academic/Research Framing ✅

Position your work as:
- Electoral transparency research
- Competitive intelligence analysis
- Market research on political advertising trends
- Documentation for historical and academic purposes

**Legal Protection:** Research and transparency activities have strong protections under Brazilian law (Constitution Art. 5º, XIV; Lei de Acesso à Informação)

### Strategy 4: Cooperation with Authorities

If ever questioned:
- ✅ Demonstrate you're using public API data
- ✅ Show legitimate research purpose
- ✅ Explain non-public, non-redistributive use
- ✅ Provide transparency about methods
- ✅ Show compliance with removal tracking

**Attitude:** Cooperative transparency researcher, not adversarial republisher

---

## Specific TSE Scenarios

### Scenario 1: TSE Orders Ad Removal

**What Happens:**
1. TSE identifies violation in political ad
2. TSE orders Meta to remove ad
3. Meta removes ad from platform
4. Ad disappears from Meta Ad Library API

**Your Position:**
- ✅ You archived public data before removal (legitimate)
- ✅ Your private database maintains historical record (protected)
- ✅ You're not actively redistributing removed content (compliant)
- ✅ You can mark ad as "removed per TSE order" for research context

**Legal Risk:** **VERY LOW** - You didn't violate TSE order; the advertiser and platform did. Your archival is for research.

### Scenario 2: Someone Reports Your Database

**If authorities inquire:**

**Your Response Framework:**
1. **Source:** "All data from Meta's official public API"
2. **Purpose:** "Private research on electoral advertising trends"
3. **Use:** "Internal analysis, not public redistribution"
4. **Compliance:** "We track removal status and respect platform/TSE decisions"
5. **Legal Basis:** "Protected research activity under information access laws"

**Documentation to Provide:**
- Meta API approval confirmation
- This legal compliance document
- Evidence of private (non-public) use
- Research purpose statement
- Disclaimer implementation

**Risk Level:** **VERY LOW** - Legitimate research activity

### Scenario 3: Public Inquiry About Removed Ad

**If asked about specific removed ad:**

**Safe Response:**
```
"This ad was collected from Meta Ad Library during our research on
[date]. According to our records, it was subsequently removed from
the platform. Our database maintains historical records for research
purposes only and does not constitute republication or endorsement
of removed content."
```

**What NOT to do:**
- ❌ Don't republish the full ad publicly
- ❌ Don't share screenshots on social media
- ❌ Don't create public searchable database
- ❌ Don't claim removed ads "should still be public"

---

## Comparison: What IS Illegal vs. What You're Doing

### ❌ ILLEGAL Activities (Don't Do):

1. **Creating false political ads**
   - Criminal violation of electoral law
   - Direct TSE jurisdiction

2. **Actively redistributing TSE-removed ads to public**
   - Could be seen as defying TSE order
   - Especially if done to undermine removal

3. **Using removed ads for political campaign purposes**
   - Perpetuating banned content
   - Electoral law violation

4. **Profiting from TSE-removed content distribution**
   - Commercial exploitation of banned material
   - Possible legal liability

### ✅ YOUR Activity (Protected):

1. **Archiving publicly available data from official API**
   - Protected research activity
   - Similar to journalistic archiving

2. **Private database for competitive intelligence**
   - Legitimate business research
   - Non-public, non-redistributive

3. **Analyzing patterns and trends**
   - Academic/research purpose
   - Transparency and documentation

4. **Historical record keeping**
   - Preserving electoral history
   - Democratic transparency value

---

## Additional Legal Protections

### Brazilian Constitutional Protection

**Article 5º, XIV:**
> "é assegurado a todos o acesso à informação"
> (access to information is guaranteed to all)

**Article 220:**
> "A manifestação do pensamento, a criação, a expressão e a informação,
> sob qualquer forma, processo ou veículo não sofrerão qualquer restrição"
> (Expression and information shall not suffer restrictions)

### Lei de Acesso à Informação (12.527/2011)

Protects:
- Right to access public information
- Research using public data
- Transparency and documentation activities

### Academic/Journalistic Privilege

Courts generally protect:
- Historical documentation
- Research and analysis
- Electoral transparency initiatives
- Good faith archival for public interest

---

## Recommendations

### Immediate Actions (Already Implemented):

1. ✅ Use only Meta's official public API
2. ✅ Maintain private database (not publicly searchable)
3. ✅ Include legal disclaimers in documentation
4. ✅ Document legitimate research purpose

### Enhanced Protection (Recommended):

1. **Add removal status tracking** to database schema
2. **Implement periodic verification** to check if ads still exist
3. **Mark removed ads** with context: "Removed from platform [date]"
4. **Focus reports** on aggregated data, not individual removed ads
5. **Maintain audit log** of all data collection activities

### If You Ever Need to Share Data:

**Safe Approaches:**
- ✅ Share aggregated statistics only
- ✅ Share trends and patterns (no individual ads)
- ✅ Share with academic/research NDAs
- ✅ Share for journalistic investigation (protected activity)

**Risky Approaches:**
- ❌ Public website with searchable removed ads
- ❌ Social media posts of TSE-removed content
- ❌ Commercial sale of removed ad database
- ❌ API providing access to removed ads

---

## Conclusion

### Your Legal Risk: **VERY LOW** ✅

**Summary:**
- You're using public data from official API
- Purpose is legitimate research and intelligence
- Database is private, not publicly redistributed
- Activity protected by information access laws
- Similar to journalism, academia, transparency orgs

**Key Principle:**
> You are documenting and analyzing public information for research purposes,
> not creating, endorsing, or actively redistributing political content.
> This is protected activity under Brazilian law.

**If Ever Questioned:**
1. Show this compliance document
2. Explain research purpose
3. Demonstrate private (non-public) use
4. Emphasize Meta API as source
5. Show good faith cooperation

---

## Contact & Legal Support

**If Legal Issues Arise:**

1. **Document everything:**
   - API approval from Meta
   - Research purpose statements
   - Private use evidence
   - This compliance documentation

2. **Consult legal counsel** specializing in:
   - Electoral law (Direito Eleitoral)
   - Information access law
   - Technology/internet law

3. **Cooperate transparently** with any inquiries

4. **Frame activity** as research and transparency (which it is)

---

## Document Version

**Version:** 1.0
**Date:** January 30, 2026
**Jurisdiction:** Brazil (Federal and Electoral Law)
**Applicable Laws:**
- Constituição Federal (1988)
- Lei 9.504/97 (Lei Eleitoral)
- Lei 12.527/2011 (Lei de Acesso à Informação)
- Resoluções TSE (various)

**Legal Review:** Recommended before 2026 election period
**Next Review Date:** Before campaign period starts (August 2026)

---

**Prepared for:** Meta Ads Intelligence System
**Purpose:** Legal compliance and risk mitigation
**Disclaimer:** This document provides general legal analysis. For specific legal advice, consult a qualified attorney specializing in Brazilian electoral law.

---

*This compliance document demonstrates good faith effort to operate within legal boundaries and respect electoral regulations while conducting legitimate research activities.*
