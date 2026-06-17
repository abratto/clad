package com.example.app.steps;

import org.junit.platform.suite.api.ConfigurationParameter;
import org.junit.platform.suite.api.IncludeEngines;
import org.junit.platform.suite.api.SelectClasspathResource;
import org.junit.platform.suite.api.Suite;

import static io.cucumber.junit.platform.engine.Constants.GLUE_PROPERTY_NAME;

/**
 * Cucumber JUnit Platform Suite runner.
 *
 * <p>Discovers {@code .feature} files under {@code src/test/resources/features/}
 * and glues them to step definitions in this package.
 *
 * <p>This is the JUnit 5 entry point for the Gherkin track of CLAD's outer-red
 * flow tests. It is the executable equivalent of the markdown flow-test specs
 * that the native track produces via {@code @MicronautTest} + {@code @Test}.
 */
@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(key = GLUE_PROPERTY_NAME, value = "com.example.app.steps")
public class CucumberTest {
}
