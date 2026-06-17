export default function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="mt-2 text-sm text-gray-500">Coming in a later phase.</p>
    </div>
  );
}
