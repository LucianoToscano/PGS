import { cooldown } from '../content.js';
import { ui } from '../uiText.js';

// Community cooldown guidance: a short explainer, two expandable action lists,
// and a compact distance/wait tables. All values are framed as estimates.
export default function Cooldown() {
  return (
    <section className="section" id="cooldown" aria-labelledby="cooldown-heading">
      <div className="section__head">
        <p className="section__num">{ui.cooldown.number}</p>
        <h2 id="cooldown-heading" className="section__title">
          {ui.cooldown.title}
        </h2>
        <p className="section__lead">{cooldown.intro}</p>
      </div>

      <div className="cooldown__groups">
        <details className="cooldown__group" open>
          <summary>
            <span>{ui.cooldown.triggers}</span>
            <span className="faq__mark" aria-hidden="true" />
          </summary>
          <ul className="cooldown__list cooldown__list--trigger">
            {cooldown.triggers.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>

        <details className="cooldown__group">
          <summary>
            <span>{ui.cooldown.safe}</span>
            <span className="faq__mark" aria-hidden="true" />
          </summary>
          <ul className="cooldown__list cooldown__list--safe">
            {cooldown.safe.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>
      </div>

      <figure className="cooldown__chart">
        <figcaption className="cooldown__chart-cap">
          {ui.cooldown.chartCaption}
        </figcaption>
        <div className="cooldown__tables">
          {[cooldown.chart.slice(0, 15), cooldown.chart.slice(15)].map((rows, index) => (
            <div className="cooldown__table-wrap" key={index}>
              <table className="cooldown__table">
                <caption className="visually-hidden">{ui.cooldown.tableCaption(index + 1)}</caption>
                <thead><tr><th scope="col">{ui.cooldown.distance}</th><th scope="col">{ui.cooldown.wait}</th></tr></thead>
                <tbody>{rows.map(row => (
                  <tr key={row.km}><th scope="row">{row.km}</th><td>{row.wait}</td></tr>
                ))}</tbody>
              </table>
            </div>
          ))}
        </div>
      </figure>

      <p className="cooldown__note">
        {ui.cooldown.note}
      </p>
    </section>
  );
}
