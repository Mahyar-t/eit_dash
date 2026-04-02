import type { DatasetCard } from '../types/load';

type InfoCardProps = {
  card: DatasetCard;
  onRemove?: (label: string) => void;
};

export function InfoCard({ card, onRemove }: InfoCardProps) {
  return (
    <article className="glass-card info-card">
      <div className="info-card__body">
        <div className="info-card__header">
          <h4 className="card-title">{card.title}</h4>
          {onRemove ? (
            <button
              type="button"
              className="glass-button glass-button--ghost info-card__remove"
              onClick={() => onRemove(card.label)}
            >
              Remove
            </button>
          ) : null}
        </div>
        <table className="info-table">
          <tbody>
            {card.rows.map((row) => (
              <tr key={`${card.label}-${row.label}`}>
                <td className="info-table__label">{row.label}</td>
                <td className="info-table__value">{String(row.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
