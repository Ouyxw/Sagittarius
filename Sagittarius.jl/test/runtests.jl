using Test
using Sagittarius

@testset "Sagittarius native release contract" begin
    register = chain_register(2; spacing=2.0, C6=64.0)
    @test length(register.atoms) == 2
    @test interaction_matrix(register) == [0.0 1.0; 1.0 0.0]

    pulse = compile_pulse(ConstantPulse(2.5, 1.0))
    @test pulse(0.5) == 2.5
    @test pulse(1.5) == 0.0

    basis_states, basis_mapping = reduced_basis(register; blockade_radius=1.0)
    @test 0 in basis_states
    @test length(basis_states) == 4
    @test basis_mapping[0] == 1
end
