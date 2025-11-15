export default function IntakeNewLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-4">
      {children}
    </div>
  );
}

