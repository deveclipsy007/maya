-- Schema SQL para Maya HopeCann
-- Execute este script no seu Supabase para criar as tabelas necessárias

-- Tabela de médicos
CREATE TABLE medicos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    especialidade VARCHAR(255) DEFAULT 'Cannabis Medicinal',
    crm VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    telefone VARCHAR(20),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de horários disponíveis
CREATE TABLE horarios_disponiveis (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    medico_id UUID REFERENCES medicos(id),
    medico_nome VARCHAR(255),
    data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
    disponivel BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de agendamentos
CREATE TABLE agendamentos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    paciente_nome VARCHAR(255) NOT NULL,
    paciente_telefone VARCHAR(20) NOT NULL,
    paciente_email VARCHAR(255),
    medico_id UUID REFERENCES medicos(id),
    data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
    meet_link VARCHAR(500),
    status VARCHAR(50) DEFAULT 'agendado',
    observacoes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inserir médicos exemplo
INSERT INTO medicos (nome, especialidade, crm, email, telefone) VALUES
('Dr. Carlos Silva', 'Cannabis Medicinal', 'CRM-SP 123456', 'carlos@hopecann.com', '(11) 99999-0001'),
('Dra. Ana Santos', 'Cannabis Medicinal', 'CRM-RJ 789012', 'ana@hopecann.com', '(21) 99999-0002'),
('Dr. João Oliveira', 'Cannabis Medicinal', 'CRM-MG 345678', 'joao@hopecann.com', '(31) 99999-0003');

-- Inserir horários exemplo (próximos 7 dias)
INSERT INTO horarios_disponiveis (medico_id, medico_nome, data_hora) 
SELECT 
    m.id,
    m.nome,
    NOW() + (INTERVAL '1 day' * generate_series(1, 7)) + (INTERVAL '1 hour' * generate_series(9, 17))
FROM medicos m
WHERE m.ativo = true;

-- Políticas RLS (Row Level Security) - opcional
ALTER TABLE medicos ENABLE ROW LEVEL SECURITY;
ALTER TABLE horarios_disponiveis ENABLE ROW LEVEL SECURITY;
ALTER TABLE agendamentos ENABLE ROW LEVEL SECURITY;

-- Política para permitir leitura pública (ajuste conforme necessário)
CREATE POLICY "Permitir leitura pública" ON medicos FOR SELECT USING (true);
CREATE POLICY "Permitir leitura pública" ON horarios_disponiveis FOR SELECT USING (true);
CREATE POLICY "Permitir inserção pública" ON agendamentos FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir leitura pública" ON agendamentos FOR SELECT USING (true);
