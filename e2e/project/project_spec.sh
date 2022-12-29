Describe 'init'
  It 'initializes without error'
    When call sntl init test python
    The status should be success
  End

  It 'creates templated files and directories'
    The path "policy.json" should be file
    The path "Dockerfile" should be file
    The path "src" should be directory
  End
End

# Describe 'build'
#   image_id() {
#     docker images test:cwi -q
#   }

#   It 'builds without error'
#     When call sntl build
#     The error should be present
#     The status should be success
#   End

#   It 'produced a cwi'
#     When call sntl ls
#     The status should be success
#     The output should include $(image_id)
#   End
# End

Describe 'publish'
  It 'logs into to ecr'
    When call sntl login
    The status should be success
    The error should be present
    The output should be present
  End

  It 'publishes the image'
    When call sntl publish
    The status should be success
    The error should be present
    The output should be present
  End
End

Describe 'deploy'
  It 'deploys the lambda'
    When call sntl deploy aws
    The status should be success
    The output should be present
  End
End

# Describe 'tags'

# End

# Describe 'env'

# End

Describe 'destroy'
  it 'destroys the lambda'
    When call sntl destroy aws
    The status should be success
    The output should be present
  End
End