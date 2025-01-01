# Change to your repo folder
cd "C:\my-project"

# Ensure Git identity is set
git config user.name "scaramucci"
git config user.email "dudeibi@gmail.com"

# Parameters
$totalCommits = 204
$startDate = Get-Date "2025-01-01"
$endDate   = Get-Date "2025-12-31"

# Calculate all dates in 2025
$allDates = @()
$currentDate = $startDate
while ($currentDate -le $endDate) {
    $allDates += $currentDate
    $currentDate = $currentDate.AddDays(1)
}

# Shuffle dates randomly
$rand = New-Object System.Random
$shuffledDates = $allDates | Sort-Object { $rand.Next() }

# Pick $totalCommits dates
$commitDates = $shuffledDates[0..($totalCommits - 1)] | Sort-Object

# Make sure at least one commit every 2 days
for ($i = 1; $i -lt $commitDates.Count; $i++) {
    if (($commitDates[$i] - $commitDates[$i-1]).Days -gt 2) {
        # Fill the gap with extra dates
        $gapDays = ($commitDates[$i] - $commitDates[$i-1]).Days
        for ($j = 1; $j -lt $gapDays; $j++) {
            if ($commitDates.Count -lt $totalCommits) {
                $commitDates += $commitDates[$i-1].AddDays($j)
            }
        }
    }
}

# Sort all final commit dates
$commitDates = $commitDates | Sort-Object

# Make sure there is at least one file to commit
$dummyFile = "dummy.txt"
if (!(Test-Path $dummyFile)) {
    New-Item -ItemType File -Name $dummyFile -Force | Out-Null
}

# Loop through dates and create commits
$commitNum = 1
foreach ($d in $commitDates) {
    Write-Host "Creating commit $commitNum of $totalCommits for date $($d.ToString('yyyy-MM-dd'))"

    # Update dummy file to have unique content
    Add-Content $dummyFile "Commit $commitNum at $($d.ToString('yyyy-MM-dd HH:mm:ss'))"

    # Set GIT_AUTHOR_DATE and GIT_COMMITTER_DATE
    $env:GIT_AUTHOR_DATE = $d.ToString("yyyy-MM-ddT12:00:00")
    $env:GIT_COMMITTER_DATE = $d.ToString("yyyy-MM-ddT12:00:00")

    git add $dummyFile
    git commit -m "Commit $commitNum for $($d.ToString('yyyy-MM-dd'))"

    $commitNum++
}

# Push all commits to origin/main via SSH
git push origin main

Write-Host "All $totalCommits commits have been created and pushed successfully!"