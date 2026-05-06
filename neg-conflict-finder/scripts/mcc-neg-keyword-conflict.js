/**
 * ─────────────────────────────────────────────────────────────────────
 *  MCC Negative Keyword Conflict Finder
 *
 *  Derivative work by Kurt Henninger / Fourteen Web Media
 *  https://fourteenwebmedia.com  ·  https://github.com/fourteenwm/ppc-ai-skills
 *
 *  Based on Google's official Negative Keyword Conflict reference script.
 *  Substantial modifications (see @changelog v2.0+):
 *    - Ported from single-account to MCC-wide with label-based filtering
 *    - Added MCC-level shared list support
 *    - Added account-level negative keyword detection (with graceful degradation)
 *    - Fixed phrase-vs-exact blocking detection bug (subsequence match)
 *    - Fixed shared-list keyword-loss regression
 *    - Added optional spend filter to skip dormant accounts
 *
 *  Distributed under the original Apache 2.0 license (preserved below).
 * ─────────────────────────────────────────────────────────────────────
 */

// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @name MCC Negative Keyword Conflict Finder
 * @overview Identifies conflicts between positive keywords and negative keywords
 *           (Ad Group, Campaign, Shared List, and MCC Shared List levels) 
 *           across multiple Google Ads accounts within an MCC, filtered by an 
 *           account label. Outputs the conflicts to a single Google Sheet.
 * @author Google Ads Scripts Team & Gemini
 * @version 4.0
 * @changelog
 *  - 4.0: Three changes:
 *         (a) Fixed PHRASE-negative-vs-EXACT-positive detection. The previous
 *             logic required exact text equality, which missed real conflicts
 *             like phrase-neg "amberglen" vs exact-pos [apartments amberglen].
 *             The negative still fully blocks every query the exact positive
 *             can match. Now uses isSubsequence() for ALL positive match types
 *             under a phrase negative, matching Google Ads' actual blocking
 *             behavior.
 *         (b) Added optional spend filter so accounts that haven't spent in the
 *             recent date range (default LAST_7_DAYS) are skipped. Cuts noise
 *             from label-tagged accounts that have cancelled budget. Toggle via
 *             REQUIRE_RECENT_SPEND. Implemented as a per-account check using
 *             `account.getStatsFor(DATE_RANGE).getCost()` -- modern Google Ads
 *             Scripts no longer support `forDateRange()` or metric filters on
 *             `MccApp.accounts()` (the customer_client resource rejects
 *             `metrics.cost_micros` in WHERE).
 *         (c) Fixed shared-list keyword-loss regression introduced in v3. The
 *             early-skip in fetchSharedNegativeLists was checking
 *             `cache.sharedLists[listId]`, which made every row AFTER the first
 *             one for a given list silently drop -- because the cache entry
 *             created by the first row caused every subsequent keyword in that
 *             list to be skipped. Result: every shared list ended up with only
 *             its first keyword, and ~99% of shared-list conflicts (incl. big
 *             lists like "GS Negatives - MCC") disappeared from the output. Now
 *             only skips when the list was actually MCC-seeded (isMccList: true).
 *             MCC-seeded entries are now marked with `isMccList: true` so the
 *             skip is precise.
 *         (d) Made fetchAccountNegatives non-fatal. The customer_negative_criterion
 *             keyword.text/match_type fields are rejected by the current Ads
 *             Scripts runtime ("UNRECOGNIZED_FIELD"), which was bubbling up
 *             through buildDataCache and causing every account to be skipped --
 *             so the sheet ended up with zero conflict rows even though all
 *             other data fetched fine. Now the failure is caught at TWO
 *             levels: (i) around AdsApp.search() inside fetchAccountNegatives
 *             for the eager case, and (ii) around the call site in
 *             buildDataCache to catch the lazy hasNext() failure (the runtime
 *             defers query execution until iteration, so search() doesn't
 *             throw -- hasNext() does). Either way, processing continues with
 *             an empty account-level-negatives list. Ad-group, campaign, and
 *             shared-list conflicts are still detected normally. Account-level
 *             negative keyword conflicts will be unsupported until Google fixes
 *             the field path or until this script is rewritten against a
 *             different field schema.
 *  - 3.0: Added support for MCC-level shared negative keyword lists.
 *  - 2.0: Added support for account-level negative keywords.
 *  - 1.0: Initial version for MCC, based on single-account script.
 */

// --- Configuration ---
//
// REQUIRED: Set ACCOUNT_LABEL to a label you've applied to the accounts you
// want to process. The script only iterates accounts under your MCC that
// carry this label. (To label accounts: in your MCC, select accounts → Apply
// label → create or pick a label.)
//
// OPTIONAL: Set SHEET_URL to write into an existing Google Sheet. Leave it
// blank to have the script create a fresh sheet on each run.

const SHEET_URL = '';                             // <-- Optional: paste your Google Sheet URL here
const TAB_NAME = 'MCC Negative Conflicts';
const ACCOUNT_LABEL = 'YOUR_ACCOUNT_LABEL';       // <-- REQUIRED: replace with your MCC account label
const HEADERS = ['Account Name', 'Conflicting Negative Keyword', 'Level & Location', 'Blocked Positive Keywords'];

// Optional: skip accounts that have NOT spent in the recent date range. Useful
// when label-tagged accounts have cancelled budget and add noise to results.
// Set REQUIRE_RECENT_SPEND = false to disable this filter and process every
// labeled account regardless of spend.
//
// Implemented per-account via `account.getStatsFor(RECENT_SPEND_DATE_RANGE)`
// because modern Google Ads Scripts disallow forDateRange() and metric WHERE
// filters on MccApp.accounts() selectors.
const REQUIRE_RECENT_SPEND = true;
const RECENT_SPEND_DATE_RANGE = 'LAST_7_DAYS'; // accepts: TODAY, YESTERDAY, LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH, ALL_TIME, etc.
const MIN_RECENT_SPEND = 0; // dollars (account currency). 0 = "any spend > 0".

// --- Main MCC Function ---
function main() {
    const ss = getSpreadsheet(SHEET_URL);
    const sheet = ss.getSheetByName(TAB_NAME) || ss.insertSheet(TAB_NAME);
    sheet.clearContents(); // Clear previous results
    sheet.appendRow(HEADERS); // Add headers first - Note: appendRow is okay for single header row

    Logger.log('Fetching MCC-level shared negative lists...');
    const mccSharedListsCache = fetchMccSharedNegativeLists();
    Logger.log(`Found ${Object.keys(mccSharedListsCache).length} MCC-level shared lists.`);

    Logger.log(`Starting MCC Negative Keyword Conflict Check for accounts with label: "${ACCOUNT_LABEL}"...`);

    // Modern Google Ads Scripts only allow filtering MccApp.accounts() by label,
    // name, customer ID, etc. -- NOT by metrics. Spend-filtering happens per-account
    // below via account.getStatsFor(RECENT_SPEND_DATE_RANGE).
    const accountSelector = MccApp.accounts()
        .withCondition(`LabelNames CONTAINS "${ACCOUNT_LABEL}"`)
        .get();

    Logger.log(`Found ${accountSelector.totalNumEntities()} accounts with label "${ACCOUNT_LABEL}".`);
    if (REQUIRE_RECENT_SPEND) {
        Logger.log(`Spend filter ON: accounts with cost <= $${MIN_RECENT_SPEND} over ${RECENT_SPEND_DATE_RANGE} will be skipped.`);
    } else {
        Logger.log('Spend filter OFF: processing all label-tagged accounts.');
    }

    let skippedNoSpend = 0;
    while (accountSelector.hasNext()) {
        const account = accountSelector.next();
        const accountName = account.getName() || `Account ID: ${account.getCustomerId()}`; // Fallback to ID if name is unavailable

        // Per-account spend filter (replaces the unsupported forDateRange()/metric WHERE on MccApp.accounts()).
        if (REQUIRE_RECENT_SPEND) {
            try {
                const stats = account.getStatsFor(RECENT_SPEND_DATE_RANGE);
                const cost = stats.getCost();
                if (cost <= MIN_RECENT_SPEND) {
                    Logger.log(`Skipping ${accountName} (ID: ${account.getCustomerId()}) -- spend ${cost} <= ${MIN_RECENT_SPEND} over ${RECENT_SPEND_DATE_RANGE}.`);
                    skippedNoSpend++;
                    continue;
                }
            } catch (e) {
                Logger.log(`Warning: could not read stats for ${accountName}: ${e}. Processing anyway.`);
            }
        }

        // Select the child account to operate on it
        MccApp.select(account);
        Logger.log(`--- Processing Account: ${accountName} (ID: ${account.getCustomerId()}) ---`);

        const accountStartTime = new Date();
        try {
            // Pass the MCC-level list cache to the function that builds the account-specific cache
            const dataCache = buildDataCache(mccSharedListsCache); 

            if (!dataCache) {
                Logger.log(`Could not build data cache for account ${accountName}. Skipping.`);
                continue; // Move to the next account
            }


            const accountConflicts = findConflicts(dataCache); // Find conflicts within this account

            if (accountConflicts.length > 0) {
                Logger.log(`Found ${accountConflicts.length} conflicts in account ${accountName}.`);
                // Add account name to each conflict row and prepare for writing
                const conflictsToWrite = accountConflicts.map(conflictRow => {
                    return [accountName, ...conflictRow]; // Prepend account name
                });
                // Write conflicts for this account immediately
                outputConflictsToSheet(sheet, conflictsToWrite);
            } else {
                Logger.log(`No conflicts found in account ${accountName}.`);
                // Prepare and write the 'NO CONFLICT' row for this account immediately
                const noConflictRow = [[accountName, 'NO CONFLICT', '', '']];
                outputConflictsToSheet(sheet, noConflictRow);
            }

        } catch (e) {
            Logger.log(`❌ Error processing account ${accountName}: ${e}`);
            Logger.log(`Stack: ${e.stack}`);
            // Optionally add an error row to the sheet or just log and continue
            // allConflicts.push([accountName, 'Error Processing Account', e.message, '']);
        } finally {
            const accountEndTime = new Date();
            const accountDuration = (accountEndTime.getTime() - accountStartTime.getTime()) / 1000; // Duration in seconds
            Logger.log(`--- Finished Processing Account: ${accountName} (Duration: ${accountDuration.toFixed(2)} seconds) ---`);
        }
    } // End account loop

    if (REQUIRE_RECENT_SPEND) {
        Logger.log(`Spend filter summary: skipped ${skippedNoSpend} account(s) with no recent spend.`);
    }

    // Results are written incrementally within the loop now.
    // Log the final sheet URL.
    Logger.log(`Finished processing all accounts. Results available at: ${ss.getUrl()}`);

    Logger.log('MCC script finished.');
}


// --- Data Fetching and Caching ---

/**
 * Fetches shared negative lists that exist at the MCC level.
 * This function must be run while the MCC account is still selected.
 * @return {object} A cache of MCC-level shared lists. { listId: { name: '...', negatives: [...] } }
 */
function fetchMccSharedNegativeLists() {
    const mccListCache = {};
    // This query is identical to the one in fetchSharedNegativeLists, but it runs
    // at the MCC level to capture lists owned by the manager account.
    const listQuery = `
      SELECT
        shared_set.id,
        shared_set.name,
        shared_criterion.keyword.text,
        shared_criterion.keyword.match_type
      FROM shared_criterion
      WHERE shared_set.type = 'NEGATIVE_KEYWORDS'
        AND shared_set.status = 'ENABLED'
        AND shared_criterion.type = 'KEYWORD'`;

    const report = AdsApp.search(listQuery);
    while (report.hasNext()) {
        try {
            const row = report.next();
            const sharedSetData = row.sharedSet || {};
            const criterionData = row.sharedCriterion || {};
            const keywordData = criterionData.keyword || {};
            const listId = sharedSetData.id;
            const listName = sharedSetData.name;
            const keywordText = keywordData.text;
            const keywordMatchType = keywordData.matchType;

            if (!listId || !listName || !keywordText || !keywordMatchType) continue;

            if (!mccListCache[listId]) {
                // Mark MCC-seeded entries so fetchSharedNegativeLists can identify
                // them and skip re-processing without dropping child-level keywords.
                mccListCache[listId] = { name: listName, negatives: [], isMccList: true };
            }
            const normalizedKeyword = normalizeKeyword(keywordText, keywordMatchType);
            if (normalizedKeyword) {
                mccListCache[listId].negatives.push(normalizedKeyword);
            }
        } catch (e) {
            Logger.log(`Error processing MCC shared list keyword row: ${e}`);
        }
    }
    return mccListCache;
}

/**
 * Builds a cache of positive keywords, negative keywords (all levels),
 * and shared list associations for the currently selected account.
 * @param {object} mccSharedListsCache A pre-built cache of lists from the MCC level.
 * @return {object|null} The data cache or null if fetching fails.
 */
function buildDataCache(mccSharedListsCache) {
    // Cache is built per-account
    const cache = {
        campaigns: {},
        // Start with the MCC lists, and add any account-specific lists later
        sharedLists: { ...mccSharedListsCache }, 
        accountNegatives: []
    };


    try {
        Logger.log('Fetching positive and ad group negative keywords...');
        fetchKeywords(cache);

        Logger.log('Fetching campaign negative keywords...');
        fetchCampaignNegatives(cache);

        Logger.log('Fetching shared negative keyword lists and associations...');
        fetchSharedNegativeLists(cache);

        Logger.log('Fetching account-level negative keywords...');
        // Belt-and-suspenders: any throw inside fetchAccountNegatives (including
        // lazy hasNext() failures from the broken customer_negative_criterion
        // GAQL fields) must not kill the entire data cache. Catch and continue.
        try {
            fetchAccountNegatives(cache);
        } catch (e) {
            Logger.log(`Warning: fetchAccountNegatives threw (${e}). Skipping account-level negatives for this account; ad-group, campaign, and shared-list conflicts will still be detected.`);
        }

        return cache;
    } catch (e) {
        // Log error with account context if possible (though main loop handles account name logging)
        Logger.log(`Error building data cache: ${e}`);
        Logger.log(`Stack: ${e.stack}`);
        return null;
    }
}

/**
 * Fetches positive and ad group level negative keywords using GAQL for the selected account.
 * Populates the cache.
 * @param {object} cache The data cache object for the current account.
 */
function fetchKeywords(cache) {
    // Added LIMIT 1 query for structure logging as per mega.md
    const keywordBaseQuery = `
      SELECT
        campaign.id,
        campaign.name,
        ad_group.id,
        ad_group.name,
        ad_group_criterion.keyword.text,
        ad_group_criterion.keyword.match_type,
        ad_group_criterion.negative,
        ad_group_criterion.status
      FROM keyword_view
      WHERE campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_criterion.status = 'ENABLED'
        AND ad_group_criterion.type = 'KEYWORD'`;

    // Log sample row structure
    try {
        Logger.log("Running sample keyword query for structure check...");
        const sampleIterator = AdsApp.search(keywordBaseQuery + ' LIMIT 1');
        if (sampleIterator.hasNext()) {
            const sampleRow = sampleIterator.next();
            Logger.log("Sample Row (Keyword View): " + JSON.stringify(sampleRow));
            if(sampleRow.campaign) Logger.log("Sample Campaign: " + JSON.stringify(sampleRow.campaign));
            if(sampleRow.adGroup) Logger.log("Sample AdGroup: " + JSON.stringify(sampleRow.adGroup));
            if(sampleRow.adGroupCriterion) Logger.log("Sample AdGroupCriterion: " + JSON.stringify(sampleRow.adGroupCriterion));
            if(sampleRow.adGroupCriterion && sampleRow.adGroupCriterion.keyword) Logger.log("Sample Keyword: " + JSON.stringify(sampleRow.adGroupCriterion.keyword));
        } else {
            Logger.log("Sample keyword query returned no results.");
        }
    } catch(e) {
        Logger.log(`Error running sample keyword query: ${e}`);
    }

    const fetchStartTime = new Date(); // <--- Declare START time here
    // Fetch all results
    const report = AdsApp.search(keywordBaseQuery);
    let processedCount = 0;
    let logCount = 0;

    while (report.hasNext()) {
        let row; // Define row outside try block for logging in catch
        try {
            row = report.next();
            // Access fields using camelCase as per mega.md and verified by sample log
            const campaignData = row.campaign || {};
            const adGroupData = row.adGroup || {};
            const criterionData = row.adGroupCriterion || {};
            const keywordData = criterionData.keyword || {};

            const campaignId = campaignData.id;
            const campaignName = campaignData.name;
            const adGroupId = adGroupData.id;
            const adGroupName = adGroupData.name;
            const keywordText = keywordData.text;
            const keywordMatchType = keywordData.matchType;
             // Ensure correct access to boolean 'negative' field
            const isNegative = criterionData.negative; // Should be a boolean true/false

            if (!campaignId || !adGroupId || !keywordText || !keywordMatchType) {
                 Logger.log(`Skipping keyword row due to missing essential data (Campaign/AdGroup ID, Text, MatchType): ${JSON.stringify(row)}`);
                 continue;
            }

             // Initialize Campaign Cache
            if (!cache.campaigns[campaignId]) {
                cache.campaigns[campaignId] = {
                    name: campaignName,
                    adGroups: {},
                    negatives: [],
                    sharedListNegatives: [] // { listId: '...', listName: '...' }
                };
            }

            // Initialize Ad Group Cache
            if (!cache.campaigns[campaignId].adGroups[adGroupId]) {
                cache.campaigns[campaignId].adGroups[adGroupId] = {
                    name: adGroupName,
                    positives: [],
                    negatives: []
                };
            }

            const normalizedKeyword = normalizeKeyword(keywordText, keywordMatchType);
             if (!normalizedKeyword) { // Skip if normalization failed
                 Logger.log(`Skipping keyword due to normalization failure. Original text: "${keywordText}", Type: ${keywordMatchType}`);
                 continue;
             }

            // Check the boolean value explicitly
             if (isNegative === true) {
                 cache.campaigns[campaignId].adGroups[adGroupId].negatives.push(normalizedKeyword);
             } else if (isNegative === false) {
                 cache.campaigns[campaignId].adGroups[adGroupId].positives.push(normalizedKeyword);
             } else {
                 Logger.log(`Warning: ad_group_criterion.negative was not explicitly true or false for criterion in Ad Group ${adGroupName} (ID: ${adGroupId}). Value: ${isNegative}. Assuming it's a positive keyword.`);
                 cache.campaigns[campaignId].adGroups[adGroupId].positives.push(normalizedKeyword);
             }
            processedCount++;

        } catch (e) {
             // Log row data if available
             const rowDataString = row ? JSON.stringify(row) : 'N/A';
             Logger.log(`Error processing keyword row: ${e} | Row: ${rowDataString}`);
             // Optionally log stack trace: Logger.log(`Stack: ${e.stack}`);
        }
        logCount++;
        if (logCount % 1000 === 0) { // Log progress every 1000 rows
            Logger.log(`   ...processed ${logCount} keyword rows...`);
        }
    }
    const fetchEndTime = new Date();
    const fetchDuration = (fetchEndTime.getTime() - fetchStartTime.getTime()) / 1000;
    Logger.log(`Finished processing ${processedCount} positive/ad group negative keywords for ${Object.keys(cache.campaigns).length} campaigns. (Fetch Duration: ${fetchDuration.toFixed(2)}s)`);
}


/**
 * Fetches campaign level negative keywords using GAQL for the selected account.
 * Populates the cache.
 * @param {object} cache The data cache object for the current account.
 */
function fetchCampaignNegatives(cache) {
    const campaignNegativeBaseQuery = `
      SELECT
        campaign.id,
        campaign_criterion.keyword.text,
        campaign_criterion.keyword.match_type
      FROM campaign_criterion
      WHERE campaign_criterion.negative = TRUE
        AND campaign_criterion.type = 'KEYWORD'
        AND campaign.status = 'ENABLED'
        AND campaign_criterion.status = 'ENABLED'`;

     // Log sample row structure
    try {
        Logger.log("Running sample campaign negative query for structure check...");
        const sampleIterator = AdsApp.search(campaignNegativeBaseQuery + ' LIMIT 1');
         if (sampleIterator.hasNext()) {
            const sampleRow = sampleIterator.next();
            Logger.log("Sample Row (Campaign Criterion): " + JSON.stringify(sampleRow));
            if(sampleRow.campaign) Logger.log("Sample Campaign: " + JSON.stringify(sampleRow.campaign));
            if(sampleRow.campaignCriterion) Logger.log("Sample CampaignCriterion: " + JSON.stringify(sampleRow.campaignCriterion));
            if(sampleRow.campaignCriterion && sampleRow.campaignCriterion.keyword) Logger.log("Sample Keyword: " + JSON.stringify(sampleRow.campaignCriterion.keyword));
         } else {
             Logger.log("Sample campaign negative query returned no results.");
         }
     } catch(e) {
         Logger.log(`Error running sample campaign negative query: ${e}`);
     }

    const fetchStartTime = new Date(); // <--- Declare START time here
    // Fetch all results
    const report = AdsApp.search(campaignNegativeBaseQuery);
    let processedCount = 0;
    let logCount = 0;

    while (report.hasNext()) {
        let row; // Define row outside try block for logging in catch
        try {
            row = report.next();
            // Access fields using camelCase
            const campaignData = row.campaign || {};
            const criterionData = row.campaignCriterion || {};
            const keywordData = criterionData.keyword || {};

            const campaignId = campaignData.id;
            const keywordText = keywordData.text;
            const keywordMatchType = keywordData.matchType;

            if (!campaignId || !keywordText || !keywordMatchType) {
                 Logger.log(`Skipping campaign negative row due to missing essential data (Campaign ID, Text, MatchType): ${JSON.stringify(row)}`);
                 continue;
            }

            if (cache.campaigns[campaignId]) {
                const normalizedKeyword = normalizeKeyword(keywordText, keywordMatchType);
                 if (normalizedKeyword) { // Check if normalization was successful
                     cache.campaigns[campaignId].negatives.push(normalizedKeyword);
                     processedCount++;
                 } else {
                      Logger.log(`Skipping campaign negative due to normalization failure. Original text: "${keywordText}", Type: ${keywordMatchType}, Campaign ID: ${campaignId}`);
                 }
            } else {
                // Campaign might exist but wasn't picked up by the first query (e.g., no active ad groups/keywords)
                Logger.log(`Warning: Found campaign negative for Campaign ID ${campaignId}, but campaign not found in initial keyword fetch cache. This negative will be ignored for conflict checks.`);
            }
        } catch (e) {
             const rowDataString = row ? JSON.stringify(row) : 'N/A';
             Logger.log(`Error processing campaign negative row: ${e} | Row: ${rowDataString}`);
             // Optionally log stack trace: Logger.log(`Stack: ${e.stack}`);
        }
        logCount++;
        if (logCount % 500 === 0) { // Log progress every 500 rows
             Logger.log(`   ...processed ${logCount} campaign negative rows...`);
        }
    }
    const fetchEndTime = new Date();
    const fetchDuration = (fetchEndTime.getTime() - fetchStartTime.getTime()) / 1000;
    Logger.log(`Finished processing ${processedCount} campaign negatives. (Fetch Duration: ${fetchDuration.toFixed(2)}s)`);
}


/**
 * Fetches shared negative keyword lists, their keywords, and campaign associations for the selected account.
 * Populates the cache.
 * @param {object} cache The data cache object for the current account.
 */
function fetchSharedNegativeLists(cache) {
    // 1. Get all shared lists and their negative keywords
    const listQuery = `
      SELECT
        shared_set.id,
        shared_set.name,
        shared_criterion.keyword.text,
        shared_criterion.keyword.match_type
      FROM shared_criterion
      WHERE shared_set.type = 'NEGATIVE_KEYWORDS'
        AND shared_set.status = 'ENABLED'
        AND shared_criterion.type = 'KEYWORD'
     `;
     // Skipping sample log here as shared_criterion structure is less complex and harder to sample reliably

    const listFetchStartTime = new Date(); // <--- Declare START time here
    const listReport = AdsApp.search(listQuery);
    Logger.log("Processing shared negative lists and their keywords...");
    let processedListKeywords = 0;
    while (listReport.hasNext()) {
         let row; // Define row outside try block for logging in catch
         try {
            row = listReport.next();
             // Access fields using camelCase
            const sharedSetData = row.sharedSet || {};
            const criterionData = row.sharedCriterion || {};
            const keywordData = criterionData.keyword || {};

            const listId = sharedSetData.id;
            const listName = sharedSetData.name;
            const keywordText = keywordData.text;
            const keywordMatchType = keywordData.matchType;

            // Skip rows that are missing essential data, OR rows for shared lists
            // that were already populated by the MCC seed (isMccList: true).
            //
            // IMPORTANT: do NOT skip when cache.sharedLists[listId] exists for a
            // non-MCC reason. v3 had this bug -- after the first row created a
            // cache entry for a child-level list, every subsequent keyword in
            // that same list got silently dropped, leaving each shared list with
            // only its first keyword (and ~99% of shared-list conflicts missing
            // from output).
            if (!listId || !listName || !keywordText || !keywordMatchType ||
                (cache.sharedLists[listId] && cache.sharedLists[listId].isMccList === true)) {
                 continue;
            }

            if (!cache.sharedLists[listId]) {
                cache.sharedLists[listId] = { name: listName, negatives: [], isMccList: false }; // Mark as account-level
            }
             const normalizedKeyword = normalizeKeyword(keywordText, keywordMatchType);
             if (normalizedKeyword) { // Check normalization result
                 cache.sharedLists[listId].negatives.push(normalizedKeyword);
                 processedListKeywords++;
             } else {
                 Logger.log(`Skipping shared list negative due to normalization failure. Original text: "${keywordText}", Type: ${keywordMatchType}, List ID: ${listId}`);
             }
         } catch (e) {
            const rowDataString = row ? JSON.stringify(row) : 'N/A';
            Logger.log(`Error processing shared list keyword row: ${e} | Row: ${rowDataString}`);
            // Optionally log stack trace: Logger.log(`Stack: ${e.stack}`);
         }
    }
     const listFetchEndTime = new Date();
     const listFetchDuration = (listFetchEndTime.getTime() - listFetchStartTime.getTime()) / 1000;
     Logger.log(`Finished processing ${processedListKeywords} keywords across ${Object.keys(cache.sharedLists).length} shared lists. (Fetch Duration: ${listFetchDuration.toFixed(2)}s)`);


    // 2. Get campaign associations for these lists
    Logger.log("Fetching campaign associations for shared lists...");
    const campaignListQuery = `
       SELECT
         campaign.id,
         campaign_shared_set.shared_set
       FROM campaign_shared_set
       WHERE campaign_shared_set.status = 'ENABLED'
         AND campaign.status = 'ENABLED'
         AND shared_set.type = 'NEGATIVE_KEYWORDS'
         AND shared_set.status = 'ENABLED'  -- Added status check for the shared set itself
    `;
     // Skipping sample log here as structure is straightforward

    const assocFetchStartTime = new Date(); // <--- Declare START time here
    const campaignListReport = AdsApp.search(campaignListQuery);
    let processedAssociations = 0;
     while (campaignListReport.hasNext()) {
         let row; // Define row outside try block for logging in catch
         try {
            row = campaignListReport.next();
             // Access fields using camelCase
            const campaignData = row.campaign || {};
            const campaignSharedSetData = row.campaignSharedSet || {};

            const campaignId = campaignData.id;
             // sharedSet field is the resource name like 'customers/123/sharedSets/456'
            const sharedSetResourceName = campaignSharedSetData.sharedSet;

             if (!campaignId || !sharedSetResourceName) {
                 Logger.log(`Skipping campaign shared set row due to missing essential data (Campaign ID, Set Resource Name): ${JSON.stringify(row)}`);
                 continue;
             }

             // Extract listId from resource name
             const listIdMatch = sharedSetResourceName.match(/sharedSets\/(\d+)$/);
             if (!listIdMatch || !listIdMatch[1]) {
                 Logger.log(`Could not extract list ID from resource name: ${sharedSetResourceName}. Skipping association.`);
                 continue;
             }
             const listId = listIdMatch[1];


            if (cache.campaigns[campaignId] && cache.sharedLists[listId]) {
                 // Check if already added to prevent duplicates if query returns multiple times
                 const alreadyAdded = cache.campaigns[campaignId].sharedListNegatives.some(item => item.listId === listId);
                 if (!alreadyAdded) {
                    cache.campaigns[campaignId].sharedListNegatives.push({
                        listId: listId,
                        listName: cache.sharedLists[listId].name // Store name for easier reporting
                    });
                    processedAssociations++;
                 }
            } else {
                // Log warnings only if necessary, e.g., list ID exists but list details missing
                 if (!cache.campaigns[campaignId]) {
                     // Expected if the campaign wasn't in the first query (no active keywords/adgroups)
                 }
                 if (!cache.sharedLists[listId]) {
                     // This might happen if a list is associated but has no keywords, or status mismatch.
                     Logger.log(`Warning: Found shared list association for List ID ${listId}, but list details (name/keywords) not found in cache (maybe empty or status mismatch?). Skipping association for Campaign ID ${campaignId}.`);
                 }
            }
         } catch (e) {
             const rowDataString = row ? JSON.stringify(row) : 'N/A';
             Logger.log(`Error processing campaign shared set row: ${e} | Row: ${rowDataString}`);
             // Optionally log stack trace: Logger.log(`Stack: ${e.stack}`);
         }
     }
     const assocFetchEndTime = new Date();
     const assocFetchDuration = (assocFetchEndTime.getTime() - assocFetchStartTime.getTime()) / 1000;
     Logger.log(`Finished processing ${processedAssociations} campaign-shared list associations. (Fetch Duration: ${assocFetchDuration.toFixed(2)}s)`);
}


// --- Conflict Detection Logic (Operates on the cache of a single account) ---

/**
 * Fetches account-level negative keywords from customer_negative_criterion.
 * @param {object} cache The data cache object for the current account.
 */
function fetchAccountNegatives(cache) {
    const accountNegativeQuery = `
      SELECT
        customer_negative_criterion.keyword.text,
        customer_negative_criterion.keyword.match_type
      FROM customer_negative_criterion
      WHERE customer_negative_criterion.type = 'KEYWORD'`;

    const fetchStartTime = new Date();
    let report;
    try {
        report = AdsApp.search(accountNegativeQuery);
    } catch (e) {
        // The customer_negative_criterion.keyword.text/match_type fields are
        // currently rejected by the Google Ads Scripts runtime
        // ("UNRECOGNIZED_FIELD"). Treat this as non-fatal: log once and continue
        // with an empty account-level-negatives list rather than aborting the
        // whole account's data cache and losing all the other conflict types.
        Logger.log(`Warning: account-level negatives query failed (${e}). Skipping account-level negatives for this account; ad-group, campaign, and shared-list conflicts will still be detected.`);
        return;
    }
    let processedCount = 0;
    Logger.log("Processing account-level negative keywords...");

    while (report.hasNext()) {
        try {
            const row = report.next();
            const criterion = row.customerNegativeCriterion || {};
            const keyword = criterion.keyword || {};
            const keywordText = keyword.text;
            const keywordMatchType = keyword.matchType;

            if (!keywordText || !keywordMatchType) {
                Logger.log(`Skipping account negative row due to missing essential data: ${JSON.stringify(row)}`);
                continue;
            }

            const normalizedKeyword = normalizeKeyword(keywordText, keywordMatchType);
            if (normalizedKeyword) {
                cache.accountNegatives.push(normalizedKeyword);
                processedCount++;
            } else {
                Logger.log(`Skipping account negative due to normalization failure. Original text: "${keywordText}", Type: ${keywordMatchType}`);
            }
        } catch (e) {
            Logger.log(`Error processing account negative keyword row: ${e}`);
        }
    }
    const fetchEndTime = new Date();
    const fetchDuration = (fetchEndTime.getTime() - fetchStartTime.getTime()) / 1000;
    Logger.log(`Finished processing ${processedCount} account-level negatives. (Fetch Duration: ${fetchDuration.toFixed(2)}s)`);
}


/**
 * Iterates through the cached data of a single account to find conflicts.
 * @param {object} cache The populated data cache for the current account.
 * @return {Array<Array<string>>} An array of conflict rows for this account,
 *                                  structured as: ['negDisplayText', 'Level: Name', 'posDisplayText1, posDisplayText2'].
 *                                  Account name is NOT included here; it's added in the main loop.
 */
function findConflicts(cache) {
    const conflictsOutput = []; // [['negDisplayText', 'Level: Name', 'posDisplayText1, posDisplayText2'], ...]
    Logger.log("Starting conflict analysis for the current account...");
    const analysisStartTime = new Date();
    let campaignsChecked = 0;
    let adGroupsChecked = 0;

    for (const campaignId in cache.campaigns) {
        const campaign = cache.campaigns[campaignId];
        campaignsChecked++;

        for (const adGroupId in campaign.adGroups) {
            const adGroup = campaign.adGroups[adGroupId];
            adGroupsChecked++;
            const positives = adGroup.positives; // Array of normalized { display, raw, matchType }

            if (!positives || positives.length === 0) continue; // No positives in this ad group, no conflicts possible here

            // Define location strings without account name (added later)
            const adGroupLocation = `Ad Group: ${adGroup.name} (Campaign: ${campaign.name})`;
            const campaignLocation = `Campaign: ${campaign.name}`;

            // 1. Check Ad Group Negatives
            checkLevelForConflicts(
                conflictsOutput,
                adGroup.negatives,
                positives,
                adGroupLocation
            );

            // 2. Check Campaign Negatives
            checkLevelForConflicts(
                conflictsOutput,
                campaign.negatives,
                positives,
                campaignLocation
            );

            // 3. Check Shared List Negatives applied to this campaign
            if (campaign.sharedListNegatives && campaign.sharedListNegatives.length > 0) {
                for (const listInfo of campaign.sharedListNegatives) {
                    const listId = listInfo.listId;
                    const listDetails = cache.sharedLists[listId];

                    if (listDetails && listDetails.negatives) {
                        const listName = listDetails.name || `List ID ${listId}`;
                        // Determine if the list is from the MCC or the client account
                        const listLevel = listDetails.isMccList === false ? 'Shared List' : 'MCC Shared List';
                        const locationString = `${listLevel}: ${listName} (Applied to Campaign: ${campaign.name})`;

                        checkLevelForConflicts(
                            conflictsOutput,
                            listDetails.negatives,
                            positives,
                            locationString
                        );
                    }
                }
            }

            // 4. Check Account-Level Negatives
            checkLevelForConflicts(
                conflictsOutput,
                cache.accountNegatives,
                positives,
                'Account Level'
            );

        }
        if (campaignsChecked % 50 === 0) { // Log progress every 50 campaigns
            Logger.log(`   ...conflict analysis checked ${campaignsChecked} campaigns and ${adGroupsChecked} ad groups...`);
        }
    }
    const analysisEndTime = new Date();
    const analysisDuration = (analysisEndTime.getTime() - analysisStartTime.getTime()) / 1000;
    Logger.log(`Conflict analysis complete for current account. Found ${conflictsOutput.length} potential conflicts. (Analysis Duration: ${analysisDuration.toFixed(2)}s)`);
    return conflictsOutput; // Return conflicts for this account only
}


/**
 * Helper function to check negatives at a specific level against positives.
 * Modifies the conflictsOutput array directly.
 * @param {Array<Array<string>>} conflictsOutput The array holding conflict rows for the current account.
 * @param {Array<object>} negatives Array of normalized negative keywords { display, raw, matchType }.
 * @param {Array<object>} positives Array of normalized positive keywords { display, raw, matchType }.
 * @param {string} locationString Description of where the negative keyword exists (e.g., "Campaign: X").
 */
function checkLevelForConflicts(conflictsOutput, negatives, positives, locationString) {
     if (!negatives || negatives.length === 0) return; // No negatives at this level

    for (const negative of negatives) {
        const blockedPositivesDisplay = [];
        for (const positive of positives) {
            try {
                if (negativeBlocksPositive(negative, positive)) {
                    // Store the display version of the positive keyword
                    blockedPositivesDisplay.push(positive.display);
                }
            } catch (e) {
                 // Log error with specific context
                 Logger.log(`Error during conflict check between negative "${negative.display}" and positive "${positive.display}" at ${locationString}: ${e}`);
            }
        }

        // If this negative blocked any positives, record it
        if (blockedPositivesDisplay.length > 0) {
            conflictsOutput.push([
                negative.display, // Display version of the negative
                locationString,
                blockedPositivesDisplay.join(', ') // Comma-separated list of blocked positive display texts
            ]);
        }
    }
}

/**
 * Determines if a negative keyword blocks a positive keyword based on text and match type.
 * Logic based on how Google Ads matching prevents ads from showing.
 * @param {object} negative Normalized negative keyword { display, raw, matchType }.
 * @param {object} positive Normalized positive keyword { display, raw, matchType }.
 * @return {boolean} True if the negative blocks the positive.
 */
function negativeBlocksPositive(negative, positive) {
    // Ensure raw text exists for comparison
    if (!negative || !positive || typeof negative.raw !== 'string' || typeof positive.raw !== 'string') {
        Logger.log(`Warning: Invalid keyword object passed to negativeBlocksPositive. Negative: ${JSON.stringify(negative)}, Positive: ${JSON.stringify(positive)}`);
        return false;
    }

    // Scenario 1: Negative Exact Match
    // Blocks ANY positive type if the positive keyword text *exactly* matches the negative text (case-insensitive compare via raw).
    if (negative.matchType === 'EXACT') {
        return positive.raw === negative.raw;
    }

    // Scenario 2: Negative Phrase Match
    // Blocks ANY positive type (Exact, Phrase, Broad) if the negative phrase is
    // contained as an ordered subsequence within the positive's text. An exact
    // positive only matches one literal query (its own text), so a phrase negative
    // contained within that text fully blocks the positive — same logic that
    // applies to phrase/broad positives.
    //
    // Example caught by this fix that v3 missed:
    //   PHRASE neg "amberglen" vs EXACT pos [apartments amberglen]  → conflict
    if (negative.matchType === 'PHRASE') {
        return isSubsequence(negative.raw, positive.raw);
    }

    // Scenario 3: Negative Broad Match
    // Blocks ANY positive type if *all* terms in the negative keyword are present *anywhere* within the positive keyword text.
    if (negative.matchType === 'BROAD') {
        // Use hasAllTokens for broad match check
        return hasAllTokens(negative.raw, positive.raw);
    }

    // Should not happen with valid match types from normalization
    Logger.log(`Warning: Encountered unexpected negative match type '${negative.matchType}' during conflict check for negative "${negative.display}".`);
    return false;
}


// --- Text Processing and Normalization ---

/**
 * Normalizes keyword text and match type.
 * Raw: lowercase, no modifier symbols (+), no phrase/exact wrappers ("", []), single spaces between words, trimmed.
 * Display: Includes match type symbols ([], "") for readability, based on normalized type.
 * MatchType: Simple uppercase ('EXACT', 'PHRASE', 'BROAD').
 * @param {string} text Keyword text.
 * @param {string} matchType Keyword match type (e.g., 'EXACT', 'PHRASE', 'BROAD_MATCH').
 * @return {{display: string, raw: string, matchType: string}|null} Normalized keyword object or null if text/type is invalid.
 */
function normalizeKeyword(text, matchType) {
    if (!text || typeof text !== 'string' || text.trim() === '') {
        Logger.log(`Warning: Invalid or empty keyword text received: "${text}"`);
        return null;
    }
    if (!matchType || typeof matchType !== 'string') {
         Logger.log(`Warning: Invalid match type received: ${matchType} for text: "${text}"`);
         // Attempt to default or return null based on strictness required
         return null; // More strict: require a valid match type
    }

    let raw = text.trim();
    // Normalize GAQL match types to simple uppercase (e.g., BROAD_MATCH -> BROAD)
    let normalizedMatchType = matchType.toUpperCase().replace('_MATCH', '');

    // Validate normalized match type
    if (!['EXACT', 'PHRASE', 'BROAD'].includes(normalizedMatchType)) {
        Logger.log(`Warning: Unrecognized normalized match type '${normalizedMatchType}' for text: "${text}". Defaulting to BROAD.`);
        normalizedMatchType = 'BROAD'; // Default or handle error as needed
    }


    // Clean raw text: remove wrappers based on *original* match type assumptions before normalization
    // This handles cases where text might still contain wrappers from manual input or older systems.
    if (matchType.toUpperCase().includes('PHRASE')) {
        raw = trimKeyword(raw, '"', '"');
    } else if (matchType.toUpperCase().includes('EXACT')) {
        raw = trimKeyword(raw, '[', ']');
    }

    // Remove broad match modifier '+' sign PREPENDED to words (more robustly)
    // Handle cases like "+word", " +word", "+word +another"
    raw = raw.split(' ').map(word => word.startsWith('+') ? word.substring(1) : word).join(' ');

    // Collapse multiple spaces and trim again
    raw = raw.replace(/\s+/g, ' ').trim();
    // Lowercase for case-insensitive comparison
    raw = raw.toLowerCase();

    // Final check for empty raw string after cleaning
    if (raw === '') {
         Logger.log(`Warning: Keyword text became empty after normalization. Original text: "${text}", MatchType: ${matchType}`);
         return null;
    }

    // Create display version using the cleaned, raw text and the *normalized* match type
    let display = raw;
    if (normalizedMatchType === 'PHRASE') {
        display = '"' + display + '"';
    } else if (normalizedMatchType === 'EXACT') {
        display = '[' + display + ']';
    }
    // No special display format for BROAD

    return { display: display, raw: raw, matchType: normalizedMatchType };
}


/**
 * Removes leading/trailing characters if they match exactly. Case-sensitive.
 * @param {string} text The string to trim.
 * @param {string} open The expected opening character(s).
 * @param {string} close The expected closing character(s).
 * @return {string} The trimmed string.
 */
function trimKeyword(text, open, close) {
    if (text.startsWith(open) && text.endsWith(close)) {
        // Slice from after the open char(s) to before the close char(s)
        return text.substring(open.length, text.length - close.length).trim();
    }
    return text; // Return original if no match
}

/**
 * Checks if all space-separated tokens from keywordText1 are present in keywordText2.
 * Order does not matter. Comparison is case-insensitive (expects lowercase inputs).
 * Handles empty strings gracefully.
 * @param {string} keywordText1 The 'needle' keyword text (raw, normalized, lowercase).
 * @param {string} keywordText2 The 'haystack' keyword text (raw, normalized, lowercase).
 * @return {boolean} True if all tokens from text1 are in text2.
 */
function hasAllTokens(keywordText1, keywordText2) {
    // If needle is empty/null, it technically exists in any haystack (vacuously true)
    if (!keywordText1) return true;
    // If haystack is empty/null, but needle is not, then needle cannot exist
    if (!keywordText2) return false;

    const tokens1 = keywordText1.split(' ').filter(t => t !== ''); // Filter out empty tokens
    // If needle had only spaces, tokens1 is empty, return true
    if (tokens1.length === 0) return true;

    // Create a Set of tokens from keywordText2 for efficient lookups
    const tokenSet2 = new Set(keywordText2.split(' ').filter(t => t !== ''));

    // Check if every non-empty token from keywordText1 exists in tokenSet2
    return tokens1.every(token => tokenSet2.has(token));
}

/**
 * Checks if keywordText1 appears as an ordered subsequence within keywordText2.
 * Comparison is case-insensitive (expects lowercase inputs). Checks for whole word/phrase boundaries using spaces.
 * Handles empty strings gracefully.
 * @param {string} keywordText1 The 'needle' keyword text (raw, normalized, lowercase).
 * @param {string} keywordText2 The 'haystack' keyword text (raw, normalized, lowercase).
 * @return {boolean} True if text1 is a subsequence of text2 with space padding.
 */
function isSubsequence(keywordText1, keywordText2) {
     // If needle is empty/null, it technically exists in any haystack
     if (!keywordText1) return true;
     // If haystack is empty/null, but needle is not, then needle cannot exist
     if (!keywordText2) return false;

    // Add spaces to ensure whole word/phrase matching
    // e.g., looking for "cat food" in "the big cat food bowl"
    // becomes " cat food " in " the big cat food bowl "
    return (' ' + keywordText2 + ' ').indexOf(' ' + keywordText1 + ' ') !== -1;
}


// --- Spreadsheet Handling ---

/**
 * Gets the spreadsheet object, creating one if URL is not provided or invalid.
 * Uses a consistent naming convention for new sheets.
 * @param {string} url The URL of the spreadsheet. If empty/invalid, a new one is created.
 * @return {Spreadsheet} The spreadsheet object.
 */
function getSpreadsheet(url) {
    let ss;
    if (url && typeof url === 'string' && url.trim() !== '') {
        try {
            ss = SpreadsheetApp.openByUrl(url);
            Logger.log(`Using existing spreadsheet: ${url}`);
            return ss;
        } catch (e) {
            Logger.log(`Failed to open spreadsheet with URL: "${url}". Error: ${e}. Creating a new one instead.`);
            // Fall through to create a new one
        }
    }

    // Create a new spreadsheet if no valid URL provided or opening failed
    const sheetName = `MCC Negative Conflicts Report - ${getDateString()}`;
    ss = SpreadsheetApp.create(sheetName);
    Logger.log(`Created new spreadsheet: ${ss.getUrl()} with name "${sheetName}"`);
    // Note: Sharing is not done automatically. Owner needs to share if required.
    // Removed: ss.addEditor(Session.getEffectiveUser());
    return ss;
}

/**
 * Writes the conflict data to the spreadsheet using setValues for efficiency.
 * Starts writing below the header row (assumed to be row 1).
 * @param {Sheet} sheet The sheet object.
 * @param {Array<Array<string>>} allConflictData 2D array of conflict rows from all accounts.
 */
function outputConflictsToSheet(sheet, allConflictData) {
    if (!allConflictData || allConflictData.length === 0) {
        Logger.log("No conflict data to write to the sheet.");
        return; // Nothing to write
    }
    try {
        // Determine the range: Start at row 2 (below headers), column 1,
        // write all rows from allConflictData, ensure number of columns matches the data.
        const startRow = sheet.getLastRow() + 1; // Start writing after the last row (which includes headers or 'no conflicts' message)
        const startCol = 1;
        const numRows = allConflictData.length;
        // Use the length of the first data row to determine number of columns
        const numCols = allConflictData[0].length;

        if (numRows > 0 && numCols > 0) {
            // Get range and write data in bulk
            sheet.getRange(startRow, startCol, numRows, numCols)
                 .setValues(allConflictData);
            Logger.log(`Successfully wrote ${numRows} conflicts to the sheet.`);
        } else {
             Logger.log("Conflict data array was empty or malformed, nothing written.");
        }
    } catch (e) {
         Logger.log(`Error writing conflict data to sheet: ${e}`);
         Logger.log(`Number of rows to write: ${allConflictData.length}`);
         if (allConflictData.length > 0) {
             Logger.log(`Number of columns in first row: ${allConflictData[0].length}`);
         }
         // Optionally log stack trace: Logger.log(`Stack: ${e.stack}`);
    }
}

/**
 * Gets a formatted date string for sheet naming (YYYY-MM-DD).
 * Includes error handling for timezone issues.
 * @return {string} Formatted date string.
 */
function getDateString() {
    let timeZone;
    try {
        // Attempt to get MCC timezone first, fallback to script timezone
        timeZone = AdsApp.currentAccount() ? AdsApp.currentAccount().getTimeZone() : Session.getScriptTimeZone();
         if (!timeZone) throw new Error("Could not determine timezone."); // Force fallback if null/empty
        return Utilities.formatDate(new Date(), timeZone, 'yyyy-MM-dd');
    } catch (e) {
         Logger.log(`Error getting timezone (${e}). Defaulting to UTC date.`);
         // Fallback to UTC if timezone fails
         try {
             return Utilities.formatDate(new Date(), 'UTC', 'yyyy-MM-dd');
         } catch (formatError) {
             Logger.log(`Error formatting date even with UTC: ${formatError}. Returning static fallback.`);
             return 'YYYY-MM-DD'; // Last resort fallback
         }
    }
}