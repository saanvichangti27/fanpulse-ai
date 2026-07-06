/**
 * Country flag image via flagcdn.
 * `iso2` supports subdivisions like "gb-eng".
 */
export default function Flag({ iso2, size = 24, className = "", ...rest }) {
  if (!iso2) return null;
  const w = size <= 16 ? 20 : size <= 24 ? 40 : 80;
  return (
    <img
      src={`https://flagcdn.com/w${w}/${iso2}.png`}
      alt={iso2}
      width={size}
      height={Math.round(size * 0.66)}
      className={`inline-block rounded-[2px] object-cover shadow-[0_2px_6px_rgba(0,0,0,0.5)] ${className}`}
      loading="lazy"
      {...rest}
    />
  );
}
