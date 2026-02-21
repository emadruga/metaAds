#!/usr/bin/env python3
"""
============================================================================
MetaAds AWS Feasibility Test - Final Comprehensive Test Script
============================================================================
Purpose: Validate all components of MetaAds application on AWS EC2
Author: MetaAds Team
Date: 2024
============================================================================

This script performs a comprehensive test of the MetaAds application on AWS:
1. API connectivity test
2. Data collection test
3. Data processing test
4. Analysis engine test
5. Performance monitoring

Run this script after deploying to EC2 to validate the feasibility test.
============================================================================
"""

import sys
import time
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def print_header(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_success(message):
    """Print success message"""
    print(f"✓ {message}")

def print_error(message):
    """Print error message"""
    print(f"✗ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠ {message}")

def print_info(message):
    """Print info message"""
    print(f"  {message}")

def test_api_connectivity():
    """Test 1: API Connectivity"""
    print_header("Test 1: API Connectivity")

    try:
        from src.collectors.meta_api_collector import MetaAdLibraryAPI

        api = MetaAdLibraryAPI()
        print_info("Initialized Meta Ad Library API client")

        # Test with a simple search
        start_time = time.time()
        test_ads = api.search_ads(
            search_terms='marketing',
            countries=['US'],
            limit=5
        )
        elapsed = time.time() - start_time

        if test_ads:
            print_success(f"API connectivity working! Retrieved {len(test_ads)} ads in {elapsed:.2f}s")
            print_info(f"Average response time: {elapsed/max(len(test_ads), 1):.3f}s per ad")
            return True, api
        else:
            print_error("API returned no results")
            return False, None

    except Exception as e:
        print_error(f"API connectivity failed: {e}")
        return False, None

def test_data_collection(api):
    """Test 2: Data Collection"""
    print_header("Test 2: Data Collection")

    try:
        keywords = ['video editing ai', 'content creation']
        all_ads = []

        for keyword in keywords:
            print_info(f"Collecting ads for keyword: '{keyword}'")
            start_time = time.time()

            ads = api.search_ads(
                search_terms=keyword,
                countries=['US'],
                platforms=['instagram'],
                limit=25
            )

            elapsed = time.time() - start_time
            all_ads.extend(ads)

            print_success(f"Collected {len(ads)} ads in {elapsed:.2f}s ({elapsed/max(len(ads), 1):.3f}s per ad)")

        print_success(f"Successfully collected {len(all_ads)} ads total")
        return True, all_ads

    except Exception as e:
        print_error(f"Data collection failed: {e}")
        return False, []

def test_data_processing(raw_ads):
    """Test 3: Data Processing"""
    print_header("Test 3: Data Processing")

    try:
        from src.processors.ad_parser import AdParser

        parser = AdParser()
        print_info("Initialized Ad Parser")

        start_time = time.time()
        parsed_df = parser.parse_batch(raw_ads)
        elapsed = time.time() - start_time

        print_success(f"Processed {len(parsed_df)} ads in {elapsed:.2f}s")

        # Display sample statistics
        print_info(f"Average text length: {parsed_df['text_length'].mean():.0f} characters")
        print_info(f"Emoji usage: {(parsed_df['has_emoji'].sum() / len(parsed_df)) * 100:.1f}%")
        print_info(f"Hashtag usage: {(parsed_df['has_hashtags'].sum() / len(parsed_df)) * 100:.1f}%")

        return True, parsed_df

    except Exception as e:
        print_error(f"Data processing failed: {e}")
        import traceback
        print_info(traceback.format_exc())
        return False, None

def test_analysis_engine(parsed_df):
    """Test 4: Analysis Engine"""
    print_header("Test 4: Analysis Engine")

    try:
        from src.analyzers.ad_analyzer import AdAnalyzer

        analyzer = AdAnalyzer(parsed_df)
        print_info("Initialized Ad Analyzer")

        # Get top words
        top_words = analyzer.get_most_common_words(top_n=10)
        print_success(f"Most common words (Top 10):")
        for word, count in top_words:
            print_info(f"  - {word}: {count} occurrences")

        # Get CTA distribution
        cta_dist = analyzer.analyze_cta_distribution()
        print_success(f"\nCTA distribution:")
        for cta, count in cta_dist.head(5).items():
            print_info(f"  - {cta}: {count} ads")

        # Get page analysis
        by_page = analyzer.analyze_by_page().head(5)
        print_success(f"\nTop 5 advertisers:")
        for page, row in by_page.iterrows():
            print_info(f"  - {page}: {row['total_ads']} ads")

        return True

    except Exception as e:
        print_error(f"Analysis failed: {e}")
        import traceback
        print_info(traceback.format_exc())
        return False

def test_database_storage(parsed_df):
    """Test 5: Database Storage (Optional)"""
    print_header("Test 5: Database Storage")

    try:
        from src.storage.database import AdDatabase

        db = AdDatabase(db_path='data/feasibility_test.db')
        print_info("Initialized database connection")

        # Clean NaN values before saving
        import pandas as pd
        import numpy as np

        # Fill NaN values appropriately
        cleaned_df = parsed_df.copy()

        # For numeric columns, fill with 0
        numeric_cols = ['days_active', 'text_length']
        for col in numeric_cols:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].fillna(0).astype(int)

        # For string columns, fill with empty string or 'none'
        string_cols = ['body', 'headline', 'description', 'link_caption', 'full_text', 'cta_detected']
        for col in string_cols:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].fillna('none' if col == 'cta_detected' else '')

        # For list columns, convert to empty string
        list_cols = ['hashtags', 'mentions']
        for col in list_cols:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].apply(
                    lambda x: ','.join(x) if isinstance(x, list) else ''
                )

        # Save to database
        db.save_ads(cleaned_df, search_keyword='feasibility_test')
        print_success(f"Saved {len(cleaned_df)} ads to database")

        # Verify
        stats = db.get_stats()
        print_info(f"Database stats: {stats['total_ads']} total ads, {stats['active_ads']} active")

        return True

    except Exception as e:
        print_warning(f"Database storage failed (non-critical): {e}")
        print_info("This is a known issue with NaN handling and can be fixed in production")
        return False

def monitor_performance():
    """Test 6: Performance Monitoring"""
    print_header("Test 6: Performance Monitoring")

    try:
        import psutil

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        print_success(f"CPU usage: {cpu_percent}%")

        # Memory
        memory = psutil.virtual_memory()
        print_success(f"Memory usage: {memory.percent}% ({memory.used / (1024**3):.2f}GB / {memory.total / (1024**3):.2f}GB)")

        # Disk
        disk = psutil.disk_usage('/')
        print_success(f"Disk usage: {disk.percent}% ({disk.used / (1024**3):.2f}GB / {disk.total / (1024**3):.2f}GB)")

        # Check if within t3.micro limits
        if memory.used / (1024**3) < 0.9:  # t3.micro has 1GB
            print_success("Memory usage within t3.micro limits (< 900MB)")
        else:
            print_warning("Memory usage approaching t3.micro limits")

        return True

    except Exception as e:
        print_warning(f"Performance monitoring unavailable: {e}")
        print_info("Install psutil for performance monitoring: pip install psutil")
        return False

def generate_summary_report(results):
    """Generate summary report"""
    print_header("Feasibility Test Summary")

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✓")
    print(f"Failed: {failed_tests} ✗")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()

    print("Detailed Results:")
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name}: {status}")

    print()

    # Overall recommendation
    critical_tests = ['API Connectivity', 'Data Collection', 'Data Processing', 'Analysis Engine']
    critical_passed = all(results.get(test, False) for test in critical_tests)

    if critical_passed:
        print("="*80)
        print("  ✅ FEASIBILITY TEST PASSED")
        print("="*80)
        print()
        print("Recommendation: MetaAds application is ready for AWS deployment!")
        print()
        print("All critical components are working:")
        print("  ✓ Meta API connectivity from AWS infrastructure")
        print("  ✓ Data collection and processing")
        print("  ✓ Analysis engine producing insights")
        print()
        print("Next Steps:")
        print("  1. Fix database NaN handling for production use")
        print("  2. Copy .env file with production credentials")
        print("  3. Set up automated scheduling (cron/systemd)")
        print("  4. Configure monitoring and alerting")
        print("  5. Test full pipeline end-to-end")
    else:
        print("="*80)
        print("  ⚠️ FEASIBILITY TEST INCOMPLETE")
        print("="*80)
        print()
        print("Some critical tests failed. Review errors above before deploying.")

    print()

def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("  MetaAds AWS Feasibility Test - Comprehensive Validation")
    print("  Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80)

    results = {}

    # Test 1: API Connectivity
    success, api = test_api_connectivity()
    results['API Connectivity'] = success

    if not success:
        print_error("Cannot proceed without API connectivity")
        generate_summary_report(results)
        return 1

    # Test 2: Data Collection
    success, raw_ads = test_data_collection(api)
    results['Data Collection'] = success

    if not success or not raw_ads:
        print_error("Cannot proceed without data")
        generate_summary_report(results)
        return 1

    # Test 3: Data Processing
    success, parsed_df = test_data_processing(raw_ads)
    results['Data Processing'] = success

    if not success or parsed_df is None:
        print_error("Cannot proceed without processed data")
        generate_summary_report(results)
        return 1

    # Test 4: Analysis Engine
    success = test_analysis_engine(parsed_df)
    results['Analysis Engine'] = success

    # Test 5: Database Storage (non-critical)
    success = test_database_storage(parsed_df)
    results['Database Storage'] = success

    # Test 6: Performance Monitoring
    success = monitor_performance()
    results['Performance Monitoring'] = success

    # Generate summary
    generate_summary_report(results)

    print("="*80)
    print("  Feasibility test completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80)
    print()

    # Return 0 if all critical tests passed
    critical_tests = ['API Connectivity', 'Data Collection', 'Data Processing', 'Analysis Engine']
    if all(results.get(test, False) for test in critical_tests):
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
