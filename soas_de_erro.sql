-- ============================================================================
-- SOAs de Erro — Meta de Tempo de Análise
-- (Incidente/Erro no Sistema = soa_classificacoes_id = 4)
--
-- Regra de meta (dias úteis entre classificação e conclusão):
--   Alta  <= 7 dias    Media <= 14 dias    Baixa <= 35 dias
--
-- COMO USAR NO PGADMIN:
--   Troque as duas datas abaixo pelo período desejado.
--   Use o primeiro dia do mês como início e o primeiro dia do mês SEGUINTE
--   como fim (o fim é exclusivo). Ex.: maio/2026 -> '2026-05-01' e '2026-06-01'.
-- ============================================================================

WITH base AS (
    SELECT
        s.sequencial,
        scf.descricao                                         AS tipo,
        s.data_classificacao                                  AS data_classificacao,
        fs.nome                                               AS classificador,
        scr.descricao                                         AS criticidade,
        s.data_conclusao,
        GREATEST((
            SELECT COUNT(*)
            FROM generate_series(
                s.data_classificacao::date,
                s.data_conclusao::date,
                interval '1 day'
            ) AS d
            LEFT JOIN feriados f ON f.data_feriado = d::date
            WHERE EXTRACT(ISODOW FROM d) < 6      -- ignora sábado/domingo
              AND f.data_feriado IS NULL          -- ignora feriados
        ) - 1, 0) AS dias_uteis
    FROM soas s
    LEFT JOIN funcionarios fs        ON fs.id = s.funcionario_classificacao_id
    LEFT JOIN soa_criticidades scr   ON scr.id = s.soa_criticidade_id
    LEFT JOIN soa_classificacoes scf ON scf.id = s.soa_classificacoes_id
    WHERE s.soa_classificacoes_id = 4          -- 4 = Incidente/Erro no Sistema
      AND s.data_classificacao IS NOT NULL
      AND s.data_conclusao IS NOT NULL
      AND s.data_conclusao >= '2026-05-01'     -- <<< INÍCIO do período (inclusivo)
      AND s.data_conclusao <  '2026-06-01'     -- <<< FIM do período (exclusivo)
)

-- ----------------------------------------------------------------------------
-- 1) RESUMO POR CRITICIDADE (total, dentro da meta e % de meta)
-- ----------------------------------------------------------------------------
SELECT
    COALESCE(criticidade, 'TOTAL') AS criticidade,
    COUNT(*) AS total,
    COUNT(CASE WHEN (criticidade = 'Alta'  AND dias_uteis <= 7)
                 OR (criticidade = 'Media' AND dias_uteis <= 14)
                 OR (criticidade = 'Baixa' AND dias_uteis <= 35)
               THEN 1 END) AS dentro_meta,
    ROUND(
        100.0 * COUNT(CASE WHEN (criticidade = 'Alta'  AND dias_uteis <= 7)
                              OR (criticidade = 'Media' AND dias_uteis <= 14)
                              OR (criticidade = 'Baixa' AND dias_uteis <= 35)
                            THEN 1 END)
        / NULLIF(COUNT(*), 0),
    2) AS perc_meta
FROM base
WHERE criticidade IS NOT NULL
GROUP BY ROLLUP (criticidade)          -- ROLLUP gera uma linha extra com o TOTAL geral
ORDER BY CASE COALESCE(criticidade, 'TOTAL')
             WHEN 'Alta'  THEN 1
             WHEN 'Media' THEN 2
             WHEN 'Baixa' THEN 3
             WHEN 'TOTAL' THEN 9        -- total sempre por último
             ELSE 4 END;


-- ----------------------------------------------------------------------------
-- 2) DETALHE (um SOA por linha) — rode separado, se quiser a lista completa.
--    Copie o bloco WITH base AS (...) acima junto com este SELECT.
-- ----------------------------------------------------------------------------
-- SELECT
--     sequencial,
--     tipo,
--     data_classificacao,
--     classificador,
--     criticidade,
--     data_conclusao,
--     dias_uteis,
--     CASE WHEN (criticidade = 'Alta'  AND dias_uteis <= 7)
--              OR (criticidade = 'Media' AND dias_uteis <= 14)
--              OR (criticidade = 'Baixa' AND dias_uteis <= 35)
--            THEN TRUE ELSE FALSE END AS dentro_meta
-- FROM base
-- ORDER BY sequencial;
