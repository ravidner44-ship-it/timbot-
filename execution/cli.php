<?php
/**
 * Tell Tims / Qualtrics Survey Automation CLI
 * Interactive Runner
 */

require_once __DIR__ . '/TellTimsBot.php';

echo "================================================================\n";
echo "  🍩 TELL TIMS (TIM HORTONS) SURVEY AUTO-SOLVER (PHP)\n";
echo "================================================================\n";

$surveyCode = $argv[1] ?? '';

if (empty($surveyCode)) {
    echo "\n👉 Enter Receipt Survey Code (numbers only): ";
    $handle = fopen("php://stdin", "r");
    $surveyCode = trim(fgets($handle));
    fclose($handle);
}

$cleanedCode = preg_replace('/[^0-9]/', '', $surveyCode);
if (empty($cleanedCode)) {
    echo "[-] Error: Survey code cannot be empty.\n";
    exit(1);
}

echo "\n[*] Starting Auto-Solver for Receipt Code: $cleanedCode\n\n";

$bot = new TellTimsBot(function($log) {
    echo $log . "\n";
});

$result = $bot->solve($cleanedCode);

echo "\n================================================================\n";
if ($result['success'] && !empty($result['validation_code'])) {
    echo "  🎉🎉🎉 SURVEY COMPLETED SUCCESSFULLY! 🎉🎉🎉\n";
    echo "  --------------------------------------------------------------\n";
    echo "  🎟️  VALIDATION COUPON CODE :  [ " . $result['validation_code'] . " ]\n";
    echo "  --------------------------------------------------------------\n";
    echo "  👉 Write this code on your receipt to redeem your offer!\n";
} elseif ($result['success']) {
    echo "  [+] Survey Response:\n";
    echo "  " . $result['message'] . "\n";
} else {
    echo "  [-] RESULT / ERROR:\n";
    echo "  " . $result['message'] . "\n";
}
echo "================================================================\n";
