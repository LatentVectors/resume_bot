export default function IntakeJobLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 -mt-8">
      {children}
    </div>
  );
}

