import SettingsGuide from './SettingsGuide.jsx';
import Gallery from './Gallery.jsx';
import { indexHref } from './guideData.js';
import { ui } from '../uiText.js';

export default function Features() {
  return (
    <section className="section" id="features" aria-labelledby="features-heading">
      <div className="section__head">
        <p className="section__num">{ui.features.number}</p>
        <h2 id="features-heading" className="section__title">
          {ui.features.title}
        </h2>
        <p className="section__lead">
          {ui.features.lead}
        </p>
      </div>

      <p className="guide-back"><a className="btn btn--primary" href={indexHref}>{ui.features.guides}</a></p>
      <SettingsGuide />
      <Gallery />
    </section>
  );
}
