<?php
/**
 * Tell Tims Survey Auto-Solver Web Panel
 */
require_once __DIR__ . '/execution/TellTimsBot.php';

$response = null;
$logs = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $code = $_POST['survey_code'] ?? '';
    if (!empty($code)) {
        $bot = new TellTimsBot(function($msg) use (&$logs) {
            $logs[] = $msg;
        });
        $response = $bot->solve($code);
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tell Tims Survey Auto-Solver</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col items-center justify-center p-6">
    <div class="max-w-2xl w-full bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-8">
        <div class="flex items-center space-x-4 mb-6 pb-6 border-b border-slate-700">
            <div class="w-14 h-14 bg-red-600/20 text-red-500 rounded-xl flex items-center justify-center text-2xl border border-red-500/30">
                <i class="fa-solid fa-mug-hot"></i>
            </div>
            <div>
                <h1 class="text-2xl font-bold text-white tracking-wide">Tell Tims Survey Bot</h1>
                <p class="text-sm text-slate-400">Automated Qualtrics Feedback & Validation Code Generator</p>
            </div>
        </div>

        <form method="POST" class="space-y-5">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-2">
                    <i class="fa-solid fa-receipt mr-1 text-red-400"></i> Receipt Survey Code (Numbers Only)
                </label>
                <input 
                    type="text" 
                    name="survey_code" 
                    required 
                    placeholder="e.g. 200291702132101060437"
                    value="<?= htmlspecialchars($_POST['survey_code'] ?? '') ?>"
                    class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all font-mono"
                >
            </div>

            <button 
                type="submit" 
                class="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-semibold py-3.5 px-6 rounded-xl shadow-lg shadow-red-900/30 transition-all flex items-center justify-center space-x-2 cursor-pointer"
            >
                <i class="fa-solid fa-bolt"></i>
                <span>Generate Validation Coupon</span>
            </button>
        </form>

        <?php if ($response !== null): ?>
            <div class="mt-8 space-y-4">
                <?php if ($response['success'] && !empty($response['validation_code'])): ?>
                    <div class="bg-emerald-950/40 border border-emerald-500/30 rounded-2xl p-6 text-center">
                        <span class="text-xs uppercase tracking-widest font-semibold text-emerald-400 block mb-1">Coupon Validation Code</span>
                        <div class="text-4xl font-extrabold text-emerald-400 font-mono tracking-wider py-2">
                            <?= htmlspecialchars($response['validation_code']) ?>
                        </div>
                        <p class="text-sm text-slate-300 mt-2">Write this code on your receipt to redeem your offer!</p>
                    </div>
                <?php elseif ($response['success']): ?>
                    <div class="bg-blue-950/40 border border-blue-500/30 rounded-xl p-5 text-blue-300">
                        <i class="fa-solid fa-check-circle mr-2"></i> <?= htmlspecialchars($response['message']) ?>
                    </div>
                <?php else: ?>
                    <div class="bg-rose-950/40 border border-rose-500/30 rounded-xl p-5 text-rose-300">
                        <i class="fa-solid fa-triangle-exclamation mr-2"></i> <?= htmlspecialchars($response['message']) ?>
                    </div>
                <?php endif; ?>

                <?php if (!empty($logs)): ?>
                    <div class="bg-slate-950 border border-slate-800 rounded-xl p-4">
                        <div class="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Execution Logs:</div>
                        <pre class="text-xs text-slate-300 font-mono overflow-x-auto max-h-48 whitespace-pre-wrap"><?= htmlspecialchars(implode("\n", $logs)) ?></pre>
                    </div>
                <?php endif; ?>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>
