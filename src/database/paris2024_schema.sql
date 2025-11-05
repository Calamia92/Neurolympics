-- Nouvelle structure pour les donnees Paris 2024
-- Table principale des athletes Paris 2024

CREATE TABLE IF NOT EXISTS paris2024_athletes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    country_code VARCHAR(3),
    sport VARCHAR(50) NOT NULL,
    discipline VARCHAR(100),
    events TEXT[], -- Liste des epreuves
    profile_url TEXT,
    
    -- Donnees biographiques
    date_of_birth DATE,
    age INTEGER,
    gender VARCHAR(10),
    height INTEGER, -- en cm
    weight INTEGER, -- en kg
    bio_short TEXT,
    
    -- Donnees de performance (enrichissement)
    personal_best JSONB, -- Records personnels par epreuve
    season_best JSONB,   -- Meilleures performances saison
    world_ranking INTEGER,
    recent_results JSONB, -- Resultats recents competitions
    
    -- Metadonnees
    data_source VARCHAR(50) DEFAULT 'paris2024_official',
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Index uniques
    UNIQUE(name, country, sport)
);

-- Table des epreuves/events
CREATE TABLE IF NOT EXISTS paris2024_events (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50) NOT NULL,
    discipline VARCHAR(100),
    event_name VARCHAR(150) NOT NULL,
    event_code VARCHAR(20),
    gender VARCHAR(10), -- M/F/Mixed
    event_type VARCHAR(30), -- Individual/Team/Relay
    venue VARCHAR(100),
    date_start DATE,
    date_end DATE,
    
    UNIQUE(sport, event_name, gender)
);

-- Table des participations (relation many-to-many)
CREATE TABLE IF NOT EXISTS paris2024_participations (
    id SERIAL PRIMARY KEY,
    athlete_id INTEGER REFERENCES paris2024_athletes(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES paris2024_events(id) ON DELETE CASCADE,
    
    -- Donnees specifiques a la participation
    seed_time VARCHAR(20), -- Temps de qualification
    entry_standard VARCHAR(20),
    team_role VARCHAR(30), -- Pour sports d'equipe
    
    UNIQUE(athlete_id, event_id)
);

-- Table des pays/comites olympiques
CREATE TABLE IF NOT EXISTS paris2024_countries (
    id SERIAL PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(3) NOT NULL UNIQUE,
    ioc_code VARCHAR(3),
    total_athletes INTEGER DEFAULT 0,
    flag_url TEXT,
    
    -- Metadonnees
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_athletes_country ON paris2024_athletes(country);
CREATE INDEX IF NOT EXISTS idx_athletes_sport ON paris2024_athletes(sport);
CREATE INDEX IF NOT EXISTS idx_athletes_name ON paris2024_athletes(name);
CREATE INDEX IF NOT EXISTS idx_events_sport ON paris2024_events(sport);
CREATE INDEX IF NOT EXISTS idx_participations_athlete ON paris2024_participations(athlete_id);
CREATE INDEX IF NOT EXISTS idx_participations_event ON paris2024_participations(event_id);

-- Vues utiles
CREATE OR REPLACE VIEW v_athlete_summary AS
SELECT 
    a.name,
    a.country,
    a.sport,
    a.age,
    a.gender,
    array_agg(DISTINCT e.event_name) as events,
    a.world_ranking,
    a.scraped_at
FROM paris2024_athletes a
LEFT JOIN paris2024_participations p ON a.id = p.athlete_id
LEFT JOIN paris2024_events e ON p.event_id = e.id
GROUP BY a.id, a.name, a.country, a.sport, a.age, a.gender, a.world_ranking, a.scraped_at;

CREATE OR REPLACE VIEW v_country_stats AS
SELECT 
    country,
    COUNT(*) as total_athletes,
    COUNT(DISTINCT sport) as sports_count,
    array_agg(DISTINCT sport) as sports_list,
    AVG(age) as avg_age
FROM paris2024_athletes 
WHERE age IS NOT NULL
GROUP BY country
ORDER BY total_athletes DESC;