export default function Disclaimer() {
  return (
    <div role="alert" className="bg-amber-50 border-y border-amber-200 text-amber-900 text-sm">
      <div className="max-w-6xl mx-auto px-4 py-2">
        ⚠️ <strong>Review-required tool.</strong> This assistant supports ICU clinicians. It is not
        a medical device, does not place orders, and never replaces clinical judgment. All
        outputs must be reviewed before acting.
      </div>
    </div>
  );
}
