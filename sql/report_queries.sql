-- PostgreSQL reporting queries for the risk-reporting layer.

-- Latest headline VaR/ES numbers in AUD.
select
    as_of_date,
    model,
    confidence_level,
    round(value_as_return::numeric, 6) as value_as_return,
    round(value_aud::numeric, 2) as value_aud
from risk_summary
order by as_of_date desc, model, metric;

-- One-day VaR exceptions by model for model-risk review.
select
    model,
    count(*) as observations,
    sum(is_exception::int) as exceptions,
    round(avg(is_exception::int)::numeric, 4) as exception_rate
from var_backtest
group by model
order by model;

-- Worst realised P&L days in the tested portfolio.
select
    date,
    round(portfolio_return::numeric, 5) as portfolio_return,
    round((portfolio_return * 1000000)::numeric, 2) as pnl_aud
from portfolio_returns
order by portfolio_return asc
limit 10;

-- Largest component VaR contributors.
select
    ticker,
    round(component_var_return::numeric, 6) as component_var_return,
    round(component_var_aud::numeric, 2) as component_var_aud,
    round(pct_of_total::numeric, 4) as pct_of_total
from component_var
order by component_var_aud desc;

-- Stress scenarios ranked by loss.
select
    scenario,
    description,
    round(scenario_return::numeric, 5) as scenario_return,
    round(loss_aud::numeric, 2) as loss_aud
from stress_results
order by loss_aud desc;

-- Risk limit utilisation and breaches for daily escalation.
select
    risk_type,
    dimension,
    round(observed_aud::numeric, 2) as observed_aud,
    round(limit_aud::numeric, 2) as limit_aud,
    round((utilisation_pct * 100)::numeric, 1) as utilisation_percent,
    status
from risk_limits
order by utilisation_pct desc;

-- Model validation decision table.
select
    model,
    exceptions,
    round((actual_exception_rate * 100)::numeric, 2) as exception_rate_percent,
    round(kupiec_p_value::numeric, 4) as kupiec_p_value,
    round(christoffersen_p_value::numeric, 4) as independence_p_value,
    recent_250_exceptions,
    basel_traffic_light,
    overall_status
from model_monitoring
order by model;

-- Challenger-model comparison on the common holdout period.
select
    model,
    forecast_observations,
    round(mean_quantile_loss::numeric, 7) as mean_quantile_loss,
    exception_count,
    quantile_loss_rank
from model_performance
order by quantile_loss_rank;

-- Evidence for operational-efficiency claims.
select metric, round(value::numeric, 3) as value, unit, basis, interpretation
from operational_efficiency
order by metric;

-- Trade-level AUD rates and FX sensitivities.
select
    trade_id,
    instrument_type,
    round(market_value_aud::numeric, 2) as market_value_aud,
    round(dv01_aud::numeric, 2) as dv01_aud,
    round(modified_duration::numeric, 3) as modified_duration,
    market_source
from treasury_positions
order by abs(dv01_aud) desc;

-- Full-revaluation Treasury scenario P&L after hedge offsets.
select
    scenario,
    round(sum(pnl_aud)::numeric, 2) as net_pnl_aud
from treasury_scenarios
group by scenario
order by net_pnl_aud;

-- Risk limit utilisation and breaches for daily escalation.
select
    risk_type,
    dimension,
    round(observed_aud::numeric, 2) as observed_aud,
    round(limit_aud::numeric, 2) as limit_aud,
    round((utilisation_pct * 100)::numeric, 1) as utilisation_percent,
    status
from risk_limits
order by utilisation_pct desc;

-- Model validation decision table.
select
    model,
    exceptions,
    round((actual_exception_rate * 100)::numeric, 2) as exception_rate_percent,
    round(kupiec_p_value::numeric, 4) as kupiec_p_value,
    round(christoffersen_p_value::numeric, 4) as independence_p_value,
    recent_250_exceptions,
    basel_traffic_light,
    overall_status
from model_monitoring
order by model;

-- Evidence for operational-efficiency claims.
select metric, round(value::numeric, 3) as value, unit, basis, interpretation
from operational_efficiency
order by metric;
