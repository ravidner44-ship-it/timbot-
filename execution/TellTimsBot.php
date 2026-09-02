<?php
/**
 * TellTimsBot — Smart AI-Powered Tell Tims / Qualtrics Survey Solver in PHP
 * Generated from Burp Suite Capture (ppppo)
 */

class SmartQuestionSolver
{
    public static array $positiveReviews = [
        "Great experience! The coffee was piping hot, fresh and made to perfection.",
        "Very fast and friendly service at the counter. Food was fresh and delicious!",
        "Clean store, courteous staff, and my order was ready in under a minute.",
        "The drive-thru team was wonderful and very cheerful this morning. Great start to the day!",
        "Exceptional customer service, warm breakfast sandwich and great tasting coffee as always.",
        "Order was 100% accurate and served fresh. Love this Tim Hortons location!",
        "Quick service, friendly cashier, and great tasting fresh baked goods."
    ];

    public static function getTextAnswer(string $qtext): string
    {
        $qtextLower = strtolower($qtext);
        if (preg_match('/(enjoy|like|positive|experience|feedback|comment|tell us)/i', $qtextLower)) {
            return self::$positiveReviews[array_rand(self::$positiveReviews)];
        }
        if (strpos($qtextLower, 'name') !== false && strpos($qtextLower, 'team') !== false) {
            return 'Alex';
        }
        return '';
    }

    public static function selectBestChoice(string $qid, string $qtext, array $choices): string
    {
        if (empty($choices)) {
            return '1';
        }

        $choiceItems = [];
        foreach ($choices as $k => $v) {
            $disp = is_array($v) ? ($v['Display'] ?? '') : (string)$v;
            $recode = is_array($v) ? ($v['RecodeValue'] ?? (string)$k) : (string)$k;
            $choiceItems[] = ['key' => (string)$k, 'disp' => $disp, 'recode' => (string)$recode];
        }

        $qtextLower = strtolower($qtext);

        // 1. Problem / Issues -> NO
        if (preg_match('/(problem|issue|complaint|wrong with)/i', $qtextLower)) {
            foreach ($choiceItems as $item) {
                if (strtolower($item['disp']) === 'no' || $item['recode'] === '2' || stripos($item['disp'], 'no') !== false) {
                    return $item['key'];
                }
            }
            return end($choiceItems)['key'];
        }

        // 2. Team Member Recognition -> NO (skip extra fields)
        if (stripos($qtextLower, 'recognize a team member') !== false) {
            foreach ($choiceItems as $item) {
                if (strtolower($item['disp']) === 'no' || $item['recode'] === '2') {
                    return $item['key'];
                }
            }
        }

        // 3. Visit Confirmation -> YES
        if (stripos($qtextLower, 'visit on') !== false || stripos($qtextLower, 'is your feedback related to') !== false) {
            foreach ($choiceItems as $item) {
                if (strtolower($item['disp']) === 'yes' || $item['recode'] === '1') {
                    return $item['key'];
                }
            }
        }

        // 4. Rewards / Loyalty Scan -> YES
        if (stripos($qtextLower, 'tims rewards') !== false) {
            foreach ($choiceItems as $item) {
                if (stripos($item['disp'], 'yes') !== false || $item['recode'] === '1') {
                    return $item['key'];
                }
            }
        }

        // 5. Satisfaction / Likelihood Rating -> HIGHLY SATISFIED / EXCELLENT / 5 / 1
        if (preg_match('/(satisfied|satisfaction|likelihood|recommend|rate|overall|quality|cleanliness|speed|taste|friendly)/i', $qtextLower)) {
            foreach ($choiceItems as $item) {
                $d = strtolower($item['disp']);
                if (strpos($d, 'highly satisfied') !== false || strpos($d, 'extremely satisfied') !== false || strpos($d, 'highly likely') !== false) {
                    return $item['key'];
                }
            }
            foreach ($choiceItems as $item) {
                if (strpos(strtolower($item['disp']), 'satisfied') !== false || in_array($item['recode'], ['5', '4', '1'])) {
                    return $item['key'];
                }
            }
        }

        // 6. Order Type (Drive-thru / Dine-in / Takeout)
        if (preg_match('/(order type|how did you|place your order)/i', $qtextLower)) {
            foreach ($choiceItems as $item) {
                if (preg_match('/(drive-thru|drive thru|counter|dine in|takeout)/i', $item['disp'])) {
                    return $item['key'];
                }
            }
        }

        // Default
        foreach ($choiceItems as $item) {
            if (in_array($item['recode'], ['5', '1', 'yes'])) {
                return $item['key'];
            }
        }
        return $choiceItems[0]['key'];
    }

    public static function selectMatrixAnswer(array $answers): string
    {
        if (empty($answers)) {
            return '1';
        }
        foreach ($answers as $k => $v) {
            $disp = strtolower(is_array($v) ? ($v['Display'] ?? '') : '');
            if (strpos($disp, 'highly satisfied') !== false || strpos($disp, 'extremely satisfied') !== false) {
                return (string)$k;
            }
        }
        foreach ($answers as $k => $v) {
            $disp = strtolower(is_array($v) ? ($v['Display'] ?? '') : '');
            if (strpos($disp, 'satisfied') !== false || strpos($disp, 'agree') !== false) {
                return (string)$k;
            }
        }
        return (string)array_key_first($answers);
    }
}

class TellTimsBot
{
    private string $baseUrl = 'https://rbixm.qualtrics.com';
    private string $surveyId = 'SV_3lMYn8fpUtkEu7c';
    private string $initUrl = 'https://rbixm.qualtrics.com/jfe/form/SV_3lMYn8fpUtkEu7c?CountryCode=CAN&InviteType=Coupon&SC=21';
    private string $userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
    private string $cookieFile;
    private ?string $formSessionId = null;
    private ?string $xsrfToken = null;
    private ?string $brandDataCenterUrl = null;
    private ?string $jfeVersionId = null;
    private ?string $surveyVersionId = null;
    private ?string $runtimePayload = null;
    private array $logs = [];
    private $logCallback = null;

    public function __construct(?callable $logCallback = null)
    {
        $this->logCallback = $logCallback;
        $tmpDir = __DIR__ . '/../.tmp';
        if (!is_dir($tmpDir)) {
            @mkdir($tmpDir, 0777, true);
        }
        $this->cookieFile = $tmpDir . '/cookies_' . uniqid() . '.txt';
    }

    public function __destruct()
    {
        if (file_exists($this->cookieFile)) {
            @unlink($this->cookieFile);
        }
    }

    private function log(string $msg): void
    {
        $this->logs[] = $msg;
        if (is_callable($this->logCallback)) {
            call_user_func($this->logCallback, $msg);
        }
    }

    private function request(string $url, string $method = 'GET', $data = null, array $extraHeaders = []): ?string
    {
        $ch = curl_init();
        $headers = array_merge([
            'User-Agent: ' . $this->userAgent,
            'Accept-Language: en-US,en;q=0.9',
        ], $extraHeaders);

        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);
        curl_setopt($ch, CURLOPT_COOKIEJAR, $this->cookieFile);
        curl_setopt($ch, CURLOPT_COOKIEFILE, $this->cookieFile);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);

        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            if ($data !== null) {
                $payload = is_array($data) ? json_encode($data) : $data;
                curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
            }
        }

        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($response === false || $httpCode >= 400) {
            $this->log("[-] Request failed [$httpCode]: " . ($error ?: substr((string)$response, 0, 300)));
            return null;
        }

        return $response;
    }

    public function initializeSession(): ?array
    {
        $this->log("[*] Connecting to Qualtrics survey server...");
        $html = $this->request($this->initUrl, 'GET', null, [
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        ]);

        if (!$html) {
            $this->log("[-] Failed to load initial survey page.");
            return null;
        }

        $funcIdx = strpos($html, '(function(appData)');
        if ($funcIdx === false) {
            $this->log("[-] Could not find appData function in HTML.");
            return null;
        }

        $callIdx = strpos($html, '})({', $funcIdx);
        if ($callIdx === false) {
            $this->log("[-] Could not find appData JSON in HTML.");
            return null;
        }

        $jsonStart = $callIdx + 3;
        $jsonCandidate = substr($html, $jsonStart);
        
        $data = null;
        $len = strlen($jsonCandidate);
        $braceCount = 0;
        $jsonEnd = 0;
        
        for ($i = 0; $i < $len; $i++) {
            if ($jsonCandidate[$i] === '{') {
                $braceCount++;
            } elseif ($jsonCandidate[$i] === '}') {
                $braceCount--;
                if ($braceCount === 0) {
                    $jsonEnd = $i + 1;
                    break;
                }
            }
        }

        if ($jsonEnd > 0) {
            $jsonStr = substr($jsonCandidate, 0, $jsonEnd);
            $data = json_decode($jsonStr, true);
        }

        if (!$data || !isset($data['SM'])) {
            $this->log("[-] Failed to decode appData JSON.");
            return null;
        }

        $sm = $data['SM'] ?? [];
        $this->formSessionId = $sm['FormSessionID'] ?? null;
        $this->xsrfToken = $sm['XSRFToken'] ?? null;
        $this->surveyId = $sm['SurveyID'] ?? $this->surveyId;
        $this->brandDataCenterUrl = $sm['BrandDataCenterURL'] ?? 'https://iad1.qualtrics.com';
        $this->jfeVersionId = $sm['JFEVersionID'] ?? '';
        $this->surveyVersionId = $sm['SurveyVersionID'] ?? '';
        $this->runtimePayload = $data['RuntimePayload'] ?? null;

        $initialQids = $data['QuestionIDs'] ?? ['QID167', 'QID9'];
        $initialDefs = $data['QuestionDefinitions'] ?? [];

        $this->log("[+] Established Session ID: " . $this->formSessionId);
        $this->log("[+] Security Token: " . substr((string)$this->xsrfToken, 0, 10) . "...");
        return ['qids' => $initialQids, 'defs' => $initialDefs];
    }

    public function solve(string $surveyCode): array
    {
        $surveyCode = trim(preg_replace('/[^0-9]/', '', $surveyCode));
        if (strlen($surveyCode) < 10) {
            return ['success' => false, 'validation_code' => null, 'message' => 'Invalid receipt survey code format.'];
        }

        $initData = $this->initializeSession();
        if (!$initData) {
            return ['success' => false, 'validation_code' => null, 'message' => 'Could not connect to survey backend.'];
        }

        $currentQids = $initData['qids'];
        $currentDefs = $initData['defs'];

        $postHeaders = [
            'Accept: application/json, text/javascript, */*; q=0.01',
            'Content-Type: application/json',
            'Origin: ' . $this->baseUrl,
            'Referer: ' . $this->initUrl,
            'Xsrftoken: ' . $this->xsrfToken,
            'X-Requested-With: XMLHttpRequest',
            'Sec-Fetch-Dest: empty',
            'Sec-Fetch-Mode: cors',
            'Sec-Fetch-Site: same-origin'
        ];

        $tid = 1;
        $step = 0;
        $maxSteps = 35;

        while ($step < $maxSteps) {
            $step++;
            $this->log("\n[Step $step] Answering " . count($currentQids) . " questions dynamically...");

            $questionsPayload = [];
            foreach ($currentQids as $qid) {
                $qdef = $currentDefs[$qid] ?? [];
                $qtype = $qdef['Type'] ?? null;
                $qselector = $qdef['Selector'] ?? null;
                $qtext = strip_tags($qdef['QuestionText'] ?? '');

                $qObj = $qdef;
                $qObj['Valid'] = false;
                $qObj['Active'] = true;
                $qObj['Displayed'] = true;

                if ($qid === 'QID9') {
                    $this->log("  📝 [QID9] Submitting Receipt Code: $surveyCode");
                    $qObj['Value'] = $surveyCode;
                } elseif ($qtype === 'DB' || $qselector === 'TB') {
                    $this->log("  ℹ️  [$qid] Info Screen");
                } elseif ($qtype === 'TE' || in_array($qselector, ['SL', 'ML'])) {
                    $val = SmartQuestionSolver::getTextAnswer($qtext);
                    if (!empty($val)) {
                        $this->log("  💬 [$qid] Auto-generated Comment: \"$val\"");
                    } else {
                        $this->log("  ⏭️ [$qid] Optional Text Input (Skipped)");
                    }
                    $qObj['Value'] = $val;
                    $qObj['Skipped'] = empty($val);
                } elseif ($qtype === 'Matrix' || in_array($qselector, ['Likert', 'Matrix'])) {
                    $choices = $qObj['Choices'] ?? [];
                    $answers = $qObj['Answers'] ?? [];
                    $bestAns = SmartQuestionSolver::selectMatrixAnswer($answers);
                    $ansLabel = is_array($answers[$bestAns] ?? null) ? ($answers[$bestAns]['Display'] ?? 'Top Rating') : 'Top Rating';
                    $this->log("  ⭐ [$qid] Matrix Rating (" . count($choices) . " items) => \"$ansLabel\"");

                    foreach ($choices as $cid => $cval) {
                        if (is_array($choices[$cid])) {
                            $choices[$cid]['Selected'] = true;
                        }
                    }
                    $qObj['Selected'] = null;
                } elseif (in_array($qselector, ['MAVR', 'MACOL']) || ($qtype === 'MC' && !empty($qObj['ColumnCount']))) {
                    $choices = $qObj['Choices'] ?? [];
                    $choiceKeys = array_keys($choices);
                    $selectedKeys = array_slice($choiceKeys, 0, 2);
                    $selNames = [];
                    foreach ($selectedKeys as $sk) {
                        $selNames[] = is_array($choices[$sk] ?? null) ? ($choices[$sk]['Display'] ?? $sk) : $sk;
                    }
                    $this->log("  ☑️ [$qid] Multi-Select: " . implode(', ', $selNames));
                    foreach ($choices as $k => $v) {
                        if (is_array($choices[$k])) {
                            $choices[$k]['Selected'] = in_array($k, $selectedKeys);
                        }
                    }
                    $qObj['Selected'] = null;
                } else {
                    $choices = $qObj['Choices'] ?? [];
                    $selectedChoice = SmartQuestionSolver::selectBestChoice($qid, $qtext, $choices);
                    $dispText = is_array($choices[$selectedChoice] ?? null) ? ($choices[$selectedChoice]['Display'] ?? $selectedChoice) : $selectedChoice;
                    $shortQ = (strlen($qtext) > 45) ? (substr($qtext, 0, 45) . '...') : $qtext;
                    $this->log("  🔘 [$qid] $shortQ => \"$dispText\"");

                    foreach ($choices as $k => $c) {
                        if (is_array($choices[$k])) {
                            $choices[$k]['Selected'] = ((string)$k === (string)$selectedChoice);
                        }
                    }
                    $qObj['Selected'] = (string)$selectedChoice;
                }

                $questionsPayload[$qid] = $qObj;
            }

            $body = [
                'SM' => [
                    'Resolution' => '1536x864', 'FlashVersion' => -1, 'JavaSupport' => 0, 'IsIncognito' => false,
                    'BaseServiceURL' => $this->baseUrl, 'SurveyVersionID' => $this->surveyVersionId,
                    'IsBrandEncrypted' => false, 'JFEVersionID' => $this->jfeVersionId,
                    'BrandDataCenterURL' => $this->brandDataCenterUrl, 'XSRFToken' => $this->xsrfToken,
                    'StartDate' => gmdate('Y-m-d H:i:s'), 'StartDateRaw' => (int)(microtime(true) * 1000),
                    'BrandID' => 'rbixm', 'SurveyID' => $this->surveyId, 'BrowserName' => 'Chrome',
                    'BrowserVersion' => '120.0.0.0', 'OS' => 'Windows NT 10.0',
                    'UserAgent' => $this->userAgent, 'LastUserAgent' => $this->userAgent,
                    'QueryString' => 'CountryCode=CAN&InviteType=Coupon&SC=21', 'IP' => '127.0.0.1',
                    'URL' => $this->initUrl, 'BaseHostURL' => $this->baseUrl, 'ProxyURL' => $this->initUrl,
                    'JFEDataCenter' => 'spoke9', 'dataCenterPath' => 'jfe9', 'IsPreview' => false,
                    'LinkType' => 'anonymous', 'EDFromRequest' => ['CountryCode', 'InviteType', 'SC'],
                    'FormSessionID' => $this->formSessionId, 'Q_RelevantIDFraudScore' => 0,
                    'Q_RelevantIDDuplicate' => false, 'Q_RelevantIDDuplicateScore' => 0
                ],
                'ED' => [
                    'SID' => $this->surveyId, 'SurveyID' => $this->surveyId, 'Q_URL' => $this->initUrl,
                    'UserAgent' => $this->userAgent, 'Q_CHL' => 'anonymous', 'Q_Language' => 'EN',
                    'Q_RelevantIDFraudScore' => 0, 'Q_RelevantIDDuplicate' => false,
                    'Q_RelevantIDDuplicateScore' => 0
                ],
                'EDMETA' => (object)[],
                'FormRuntime' => null,
                'RuntimePayload' => ($step === 1) ? $this->runtimePayload : null,
                'FormSessionID' => $this->formSessionId,
                'Questions' => $questionsPayload,
                'TransactionID' => $tid,
                'OverridePDPWarning' => false,
                'PageAnalytics' => (object)[],
                'ProgressState' => []
            ];

            $rand = (float)rand() / (float)getrandmax();
            $t = (int)(microtime(true) * 1000);
            $postUrl = "{$this->baseUrl}/jfe9/form/{$this->surveyId}/next?rand={$rand}&tid={$tid}&t={$t}&fs={$this->formSessionId}";

            $resJson = $this->request($postUrl, 'POST', $body, $postHeaders);
            if (!$resJson) {
                return ['success' => false, 'validation_code' => null, 'message' => 'Network request failed.'];
            }

            $respData = json_decode($resJson, true);
            if (!$respData) {
                return ['success' => false, 'validation_code' => null, 'message' => 'Invalid JSON response from server.'];
            }

            if (!empty($respData['Messages']['EOSMessage']['FinalEOSMessage'])) {
                $eosText = $respData['Messages']['EOSMessage']['FinalEOSMessage'];
                $this->log("\n[🎉] Survey Flow Reached Final Completion!");

                if (preg_match('/Validation Code:\s*([A-Z0-9]+)/i', $eosText, $match)) {
                    $valCode = trim($match[1]);
                    $this->log("[✨ SUCCESS] Validation Code: " . $valCode);
                    return [
                        'success' => true,
                        'validation_code' => $valCode,
                        'message' => 'Survey completed successfully! Validation Code: ' . $valCode
                    ];
                }

                $cleanMsg = trim(strip_tags($eosText));
                if (stripos($cleanMsg, 'already been used') !== false) {
                    return [
                        'success' => false,
                        'validation_code' => null,
                        'message' => 'This receipt survey code has ALREADY BEEN USED.'
                    ];
                }

                return ['success' => true, 'validation_code' => null, 'message' => $cleanMsg];
            }

            $nextQids = $respData['QuestionIDs'] ?? [];
            $hasNextButton = !empty($respData['NextButton']);

            if (empty($nextQids) && !$hasNextButton) {
                return ['success' => false, 'validation_code' => null, 'message' => 'Survey ended early. Code might be expired or already used.'];
            }

            $currentQids = $nextQids;
            $currentDefs = $respData['QuestionDefinitions'] ?? [];
            $tid += 2;
            usleep(350000);
        }

        return ['success' => false, 'validation_code' => null, 'message' => 'Maximum steps limit reached.'];
    }
}
