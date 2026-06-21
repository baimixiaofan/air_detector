<?php
// MongoBrowser - 极简 MongoDB Web 浏览器
require 'vendor/autoload.php';
$mongo = new MongoDB\Client('mongodb://127.0.0.1:27017');
$action = $_GET['action'] ?? 'dbs';
$db = $_GET['db'] ?? 'air_quality';
$coll = $_GET['coll'] ?? 'records';
$filter = $_GET['filter'] ?? '';
$limit = min(100, max(5, intval($_GET['limit'] ?? 20)));
?>
<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><title>MongoBrowser</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f5f7;color:#1d1d1f;padding:20px}
h1{font-size:20px;margin-bottom:16px}
.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
pre{background:#f5f5f7;padding:12px;border-radius:8px;font-size:13px;overflow-x:auto;white-space:pre-wrap;word-break:break-all}
code{font-family:'SF Mono',Consolas,monospace;font-size:13px}
table{width:100%;border-collapse:collapse;font-size:14px}
td,th{padding:8px 10px;text-align:left;border-bottom:1px solid #e5e5ea;vertical-align:top}
th{background:#f5f5f7;font-weight:600;position:sticky;top:0}
tr:hover td{background:#f0f0f5}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.nav a{color:#0066cc;text-decoration:none;padding:4px 12px;border-radius:6px;background:#fff;font-size:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.nav a:hover{background:#e8f4fd}
input,select{padding:6px 10px;border:1px solid #d1d1d6;border-radius:6px;font-size:14px}
button{padding:6px 16px;background:#0066cc;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px}
button:hover{background:#0055b3}
.info{color:#6e6e73;font-size:13px;margin-bottom:12px}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;background:#e8f4fd;color:#0066cc;font-size:12px;margin-left:6px}
</style>
</head><body>

<h1>MongoBrowser</h1>

<div class="nav">
  <a href="?action=dbs">数据库</a>
  <a href="?action=query&db=air_quality&coll=records">records</a>
  <a href="?action=query&db=air_quality&coll=daily_summary">daily_summary</a>
</div>

<?php if ($action === 'dbs'): ?>
  <div class="card">
    <div style="font-weight:600;margin-bottom:12px">数据库列表</div>
    <?php foreach ($mongo->listDatabases() as $dbInfo): if (!$dbInfo->isEmpty()): ?>
      <div style="margin-bottom:8px">
        <strong><?= htmlspecialchars($dbInfo->getName()) ?></strong>
        <span class="badge"><?= number_format($dbInfo->getSizeOnDisk() / 1024) ?> KB</span>
        <?php $dbName = $dbInfo->getName(); $dbObj = $mongo->selectDatabase($dbName); ?>
        <div style="margin:4px 0 0 20px;font-size:13px;color:#6e6e73">
          <?php foreach ($dbObj->listCollections() as $c): ?>
            <a href="?action=query&db=<?= urlencode($dbName) ?>&coll=<?= urlencode($c->getName()) ?>"
               style="color:#0066cc;margin-right:12px"><?= htmlspecialchars($c->getName()) ?></a>
          <?php endforeach; ?>
        </div>
      </div>
    <?php endif; endforeach; ?>
  </div>

<?php elseif ($action === 'query'): ?>
  <div class="card">
    <form method="get" style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
      <input type="hidden" name="action" value="query">
      <span style="font-weight:600"><?= htmlspecialchars($db) ?>.<?= htmlspecialchars($coll) ?></span>
      <input type="hidden" name="db" value="<?= htmlspecialchars($db) ?>">
      <input type="hidden" name="coll" value="<?= htmlspecialchars($coll) ?>">
      <input type="text" name="filter" value="<?= htmlspecialchars($filter) ?>" placeholder='{"device_id":"CQ_001"}' style="flex:1;min-width:200px">
      <input type="number" name="limit" value="<?= $limit ?>" style="width:80px" placeholder="条数">
      <button>查询</button>
    </form>
  </div>

  <div class="card" style="overflow-x:auto">
    <?php
    try {
      $query = [];
      if ($filter) $query = json_decode($filter, true) ?: [];
      $options = ['limit' => $limit, 'sort' => ['timestamp' => -1]];
      $cursor = $mongo->selectCollection($db, $coll)->find($query, $options);
      $docs = iterator_to_array($cursor);

      if (count($docs) === 0):
        echo '<div class="info">暂无数据</div>';
      else:
        $keys = [];
        foreach ($docs as $doc) foreach (array_keys((array)$doc) as $k) $keys[$k] = true;
        echo '<div class="info">共 ' . count($docs) . ' 条</div>';
        echo '<table><tr><th>#</th>';
        foreach ($keys as $k => $_) echo '<th>' . htmlspecialchars($k) . '</th>';
        echo '</tr>';
        $i = 0;
        foreach ($docs as $doc) {
          $i++;
          $doc = (array)$doc;
          echo '<tr><td>' . $i . '</td>';
          foreach ($keys as $k => $_) {
            $v = $doc[$k] ?? '';
            if ($k === '_id') {
              echo '<td><code>' . htmlspecialchars((string)$v) . '</code></td>';
            } elseif (is_array($v) || is_object($v)) {
              echo '<td><pre style="margin:0">' . htmlspecialchars(json_encode($v, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT)) . '</pre></td>';
            } else {
              echo '<td>' . htmlspecialchars((string)$v) . '</td>';
            }
          }
          echo '</tr>';
        }
        echo '</table>';
      endif;
    } catch (Exception $e) {
      echo '<div class="info" style="color:#ff3b30">错误: ' . htmlspecialchars($e->getMessage()) . '</div>';
    }
    ?>
  </div>
<?php endif; ?>
</body></html>
