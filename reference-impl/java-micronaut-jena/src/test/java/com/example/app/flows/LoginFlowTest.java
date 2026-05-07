package com.example.app.flows;

import com.example.app.FlowTestBase;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

/**
 * Outside-loop tests for UC-00-login.
 *
 * <p>Each test corresponds one-to-one with a scenario in
 * {@code features/UC-00-login/stages/01_usecase/output/usecase.md} and
 * the predicted token chain in
 * {@code features/UC-00-login/stages/04_implement/04c_flow-tests/output/login-flow-test.md}.
 *
 * <p>All tests are {@code @Disabled} until the inner loops in
 * {@code 04d_concept-tdd/} and {@code 04e_sync-tdd/} go green.
 */
@Disabled("TODO: enabled at end of UC-00-login stage 04e_sync-tdd")
class LoginFlowTest extends FlowTestBase {

    @Test
    void successful_login_grants_session_and_returns_token() {
        // see login-flow-test.md §successful-login
    }

    @Test
    void wrong_password_returns_401_with_non_enumerating_message() {
        // see login-flow-test.md §wrong-password
    }

    @Test
    void unknown_user_returns_same_message_as_wrong_password() {
        // see login-flow-test.md §unknown-user
    }
}
